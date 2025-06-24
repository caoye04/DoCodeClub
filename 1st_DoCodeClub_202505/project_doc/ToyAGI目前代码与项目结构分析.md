# ToyAGI目前代码与项目结构分析

[toc]

## 一、项目结构

```css
code/
├── app.py              # 主应用入口
├── requirements.txt    # 依赖包列表
├── config.py           # 配置文件
├── static/             # 静态文件目录
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/          # HTML模板
│   └── index.html
├── core/
    ├── agent.py        # Agent实现
    ├── memory.py       # 上下文记忆功能
    ├── task_manager.py # 任务管理与处理
    └── llm.py          # DeepSeek API接口

```

## 二、后端实现 `code/core`

### 1.`llm.py`

```py
import requests
import json
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL

class DeepSeekLLM:
    def __init__(self, api_key=None):
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.api_url = DEEPSEEK_API_URL
        
    def generate_response(self, messages, model="deepseek-chat", temperature=0.7, max_tokens=4000):
        """
        使用DeepSeek API生成响应
        
        Args:
            messages: 消息历史列表，格式为[{"role": "user", "content": "..."}, ...]
            model: 使用的模型名称
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成令牌数
            
        Returns:
            生成的响应文本
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error calling DeepSeek API: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
```

### 2.`memory.py`

```py
class Memory:
    def __init__(self, max_history=10):
        self.conversation_history = []
        self.max_history = max_history
        
    def add_message(self, role, content):
        """添加消息到对话历史"""
        self.conversation_history.append({"role": role, "content": content})
        # 如果历史记录超过最大长度，移除最早的消息
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)
            
    def get_conversation_context(self):
        """获取当前的对话上下文"""
        return self.conversation_history.copy()
    
    def clear(self):
        """清空对话历史"""
        self.conversation_history = []
```

### 3.`agent.py`

```py
from core.llm import DeepSeekLLM
from core.memory import Memory
from core.task_manager import TaskManager
import re

class ToyAGI:
    def __init__(self, api_key=None):
        self.llm = DeepSeekLLM(api_key)
        self.memory = Memory()
        self.task_manager = TaskManager()
        self.system_prompt = (
            "你是笃小实，一个有帮助的、自主的AI助手。"
            "你可以处理任务、维持对话，并帮助用户解决各种需求。"
            "请始终保持有帮助、准确和友好的态度。"
        )
        
    def chat(self, user_message):
        """处理用户消息并返回响应"""
        # 添加用户消息到记忆
        self.memory.add_message("user", user_message)
        
        # 准备发送给LLM的上下文
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.memory.get_conversation_context())
        
        # 获取LLM响应
        response = self.llm.generate_response(messages)
        
        # 添加助手响应到记忆
        self.memory.add_message("assistant", response)
        
        return response
    
    def process_task(self, task_description):
        """处理一个任务"""
        task = self.task_manager.add_task(task_description)
        
        # 增强系统提示，要求返回格式化代码
        enhanced_system_prompt = (
            f"{self.system_prompt}\n\n"
            "在你的回答中提供代码时，请遵循以下格式指南：\n"
            "1. 始终将代码放在带有适当语言标签的markdown代码块内。\n"
            "2. 对于Python代码，在开始处使用```python，在结束处使用```。\n"
            "3. 用适当的缩进和换行来格式化代码，使其易于阅读。\n"
            "4. 添加注释来解释代码中的复杂部分。\n"
            "5. 在适当的情况下将长代码行分成多行。"
        )
        
        # 构建任务提示
        task_prompt = f"请完成以下任务: {task_description}"
        messages = [
            {"role": "system", "content": enhanced_system_prompt},
            {"role": "user", "content": task_prompt}
        ]
        
        try:
            # 获取LLM对任务的处理结果
            result = self.llm.generate_response(messages)
            
            # 检测是否包含Python代码，如果没有明确的Markdown格式，添加格式
            if "```python" not in result and self._looks_like_python_code(result):
                result = "```python\n" + result + "\n```"
                
            task.mark_completed(result)
            return result
        except Exception as e:
            task.mark_failed(str(e))
            return f"任务处理失败: {str(e)}"
    
    def _looks_like_python_code(self, text):
        """判断文本是否可能是未格式化的Python代码"""
        python_indicators = [
            "import ", "from ", "def ", "class ", 
            "if __name__", "print(", "return ", 
            "for ", "while ", "try:", "except:"
        ]
        
        # 检查文本中是否包含Python代码特征
        for indicator in python_indicators:
            if indicator in text:
                return True
                
        # 检查是否有多行代码结构
        lines = text.split('\n')
        indent_pattern = r'^\s{2,}'
        indented_lines = 0
        
        for line in lines:
            if line.strip() and re.match(indent_pattern, line):
                indented_lines += 1
                
        # 如果有多个缩进行，可能是Python代码
        if indented_lines >= 3:
            return True
            
        return False
    
    def get_task_status(self):
        """获取所有任务的状态"""
        return [task.to_dict() for task in self.task_manager.get_all_tasks()]
```

### 4.`task_manager.py`

```py
import re
from datetime import datetime

class Task:
    def __init__(self, id, description):
        self.id = id
        self.description = description
        self.status = "pending"
        self.result = None
        self.created_at = datetime.now()
        self.completed_at = None
        self.failed_at = None
        self.error = None
        
    def mark_completed(self, result=None):
        """标记任务为已完成"""
        self.status = "completed"
        self.completed_at = datetime.now()
        self.result = result
        
    def mark_failed(self, error=None):
        """标记任务为失败"""
        self.status = "failed"
        self.failed_at = datetime.now()
        self.error = error
        
    def to_dict(self):
        """转换为字典表示"""
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "error": self.error
        }
        
class TaskManager:
    def __init__(self):
        self.tasks = []
        self.next_id = 1
        
    def add_task(self, description):
        """添加新任务"""
        task = Task(self.next_id, description)
        self.tasks.append(task)
        self.next_id += 1
        return task
        
    def get_task(self, task_id):
        """获取指定ID的任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
        
    def get_all_tasks(self):
        """获取所有任务"""
        return self.tasks
```

## 三、前端实现

### 1.`code/static/css/style.css`

```css
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 16px;
    line-height: 1.5;
    color: #333;
    background-color: #f5f5f5;
}

.container {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
}

header {
    text-align: center;
    margin-bottom: 30px;
}

header h1 {
    color: #2c3e50;
    font-size: 2.5rem;
}

header p {
    color: #7f8c8d;
    font-size: 1.2rem;
}

.tabs {
    display: flex;
    margin-bottom: 20px;
    border-bottom: 1px solid #ddd;
}

.tab-btn {
    padding: 10px 20px;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1rem;
    color: #7f8c8d;
    border-bottom: 3px solid transparent;
    transition: all 0.3s;
}

.tab-btn.active {
    color: #3498db;
    border-bottom-color: #3498db;
}

.section {
    display: none;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    padding: 20px;
}

.section.active {
    display: block;
}

#chat-container {
    display: flex;
    flex-direction: column;
    height: 70vh;
}

#chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    margin-bottom: 15px;
    background-color: #f9f9f9;
}

.message {
    margin-bottom: 15px;
    max-width: 80%;
}

.message.user {
    margin-left: auto;
}

.message.assistant {
    margin-right: auto;
}

.message-content {
    padding: 10px 15px;
    border-radius: 15px;
    position: relative;
    font-size: 16px;
    line-height: 1.5;
}

.message.user .message-content {
    background-color: #3498db;
    color: white;
    border-top-right-radius: 5px;
}

.message.assistant .message-content {
    background-color: #ecf0f1;
    color: #333;
    border-top-left-radius: 5px;
}

#chat-input-container {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

#chat-input, #task-input {
    flex: 1;
    min-height: 60px;
    padding: 10px;
    border-radius: 5px;
    border: 1px solid #ddd;
    resize: none;
    font-family: inherit;
    font-size: 1rem;
}

button {
    padding: 10px 15px;
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.3s;
}

button:hover {
    background-color: #2980b9;
}

#clear-chat-btn {
    background-color: #e74c3c;
}

#clear-chat-btn:hover {
    background-color: #c0392b;
}

#task-container {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

#new-task-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

#task-list-container {
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 15px;
    background-color: #f9f9f9;
}

#task-list {
    margin-top: 10px;
    margin-bottom: 15px;
}

.task-item {
    padding: 15px;
    border-radius: 5px;
    background-color: white;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    margin-bottom: 10px;
}

.task-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
}

.task-title {
    font-weight: bold;
}

.task-status {
    padding: 3px 8px;
    border-radius: 10px;
    font-size: 0.8rem;
}

.status-pending {
    background-color: #f39c12;
    color: white;
}

.status-completed {
    background-color: #2ecc71;
    color: white;
}

.status-failed {
    background-color: #e74c3c;
    color: white;
}

/* 任务结果样式 */
.task-result {
    margin-top: 12px;
    padding: 12px;
    background-color: #f9f9f9;
    border-radius: 6px;
    font-size: 0.95rem;
    overflow-wrap: break-word;
    border: 1px solid #eaeaea;
    max-height: 500px;
    overflow-y: auto;
}

/* 代码块统一样式 */
.code-block {
    background-color: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-family: 'Courier New', Courier, monospace;
    padding: 15px;
    margin: 10px 0;
    overflow-x: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-size: 14px;
    line-height: 1.5;
    text-align: left;
}

/* 特定语言的代码块样式 */
.code-block.python {
    background-color: #f8f8f8;
    border-left: 3px solid #3776ab;
}

.code-block.javascript {
    background-color: #fbfbf8;
    border-left: 3px solid #f7df1e;
}

.code-block.html {
    background-color: #fbfaf8;
    border-left: 3px solid #e34c26;
}

.code-block.css {
    background-color: #f8f8fa;
    border-left: 3px solid #264de4;
}

/* Markdown 样式 - 优化后 */
/* 正文文本大小统一 */
.message-content p, .message-content li, .message-content a {
    font-size: 16px;
    line-height: 1.5;
    margin-bottom: 8px;
}

/* 标题统一样式，仅轻微加粗和放大 */
.markdown-heading {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #2c3e50;
    margin-top: 16px;
    margin-bottom: 8px;
    font-weight: 600;
    line-height: 1.3;
}

/* h1 样式 */
h1.markdown-heading {
    font-size: 1.35em;
    border-bottom: 1px solid #eaecef;
    padding-bottom: 4px;
}

/* h2 样式 */
h2.markdown-heading {
    font-size: 1.25em;
    border-bottom: 1px solid #eaecef;
    padding-bottom: 3px;
}

/* h3 样式 */
h3.markdown-heading {
    font-size: 1.15em;
}

/* h4 样式 */
h4.markdown-heading {
    font-size: 1.1em;
}

/* h5 样式 */
h5.markdown-heading {
    font-size: 1.05em;
}

/* h6 样式 */
h6.markdown-heading {
    font-size: 1em;
    color: #6a737d;
}

/* 普通强调文本（加粗） */
.message-content strong {
    font-weight: 600;
}

/* 普通强调文本（斜体） */
.message-content em {
    font-style: italic;
}

/* 加载动画 */
@keyframes dots {
    0%, 20% { content: '.'; }
    40% { content: '..'; }
    60%, 100% { content: '...'; }
}

.loading::after {
    content: '.';
    display: inline-block;
    animation: dots 1.5s infinite;
}

@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
    
    .message {
        max-width: 90%;
    }
    
    #chat-input-container {
        flex-direction: column;
    }
    
    button {
        width: 100%;
    }
}
```

### 2.`code/static/js/main.js`

```js
document.addEventListener('DOMContentLoaded', function() {
    // DOM元素
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const clearChatBtn = document.getElementById('clear-chat-btn');
    const chatMessages = document.getElementById('chat-messages');
    const taskInput = document.getElementById('task-input');
    const createTaskBtn = document.getElementById('create-task-btn');
    const taskList = document.getElementById('task-list');
    const refreshTasksBtn = document.getElementById('refresh-tasks-btn');
    const tabChat = document.getElementById('tab-chat');
    const tabTasks = document.getElementById('tab-tasks');
    const chatSection = document.getElementById('chat-section');
    const tasksSection = document.getElementById('tasks-section');
    
    // 标签切换
    tabChat.addEventListener('click', function() {
        tabChat.classList.add('active');
        tabTasks.classList.remove('active');
        chatSection.classList.add('active');
        tasksSection.classList.remove('active');
    });
    
    tabTasks.addEventListener('click', function() {
        tabChat.classList.remove('active');
        tabTasks.classList.add('active');
        chatSection.classList.remove('active');
        tasksSection.classList.add('active');
        loadTasks(); // 切换到任务标签时加载任务
    });
    
    // 发送聊天消息
    function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;
        
        // 添加用户消息到聊天界面
        addMessageToChat('user', message);
        chatInput.value = '';
        
        // 添加加载指示器
        const loadingId = addLoadingMessage();
        
        // 发送到后端
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            removeLoadingMessage(loadingId);
            
            if (data.response) {
                // 格式化响应内容
                const formattedResponse = formatMarkdown(data.response);
                addFormattedMessageToChat('assistant', formattedResponse);
            } else if (data.error) {
                addMessageToChat('assistant', '错误: ' + data.error);
            }
        })
        .catch(error => {
            console.error('错误:', error);
            removeLoadingMessage(loadingId);
            addMessageToChat('assistant', '抱歉，出现了问题。请重试。');
        });
    }
    
    // 创建任务
    function createTask() {
        const description = taskInput.value.trim();
        if (!description) return;
        
        taskInput.value = '';
        
        // 显示加载状态
        const taskContainer = document.createElement('div');
        taskContainer.className = 'task-item loading';
        taskContainer.textContent = '正在创建任务...';
        taskList.prepend(taskContainer);
        
        // 发送任务到后端
        fetch('/task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ description: description })
        })
        .then(response => response.json())
        .then(data => {
            taskContainer.remove();
            loadTasks(); // 刷新任务列表
        })
        .catch(error => {
            console.error('错误:', error);
            taskContainer.textContent = '创建任务时出错';
            taskContainer.className = 'task-item error';
        });
    }
    
    // 加载任务列表
    function loadTasks() {
        taskList.innerHTML = '<div class="loading">正在加载任务...</div>';
        
        fetch('/tasks')
        .then(response => response.json())
        .then(data => {
            taskList.innerHTML = '';
            
            if (data.tasks.length === 0) {
                taskList.innerHTML = '<div class="no-tasks">暂无任务</div>';
                return;
            }
            
            // 按创建时间倒序排序
            data.tasks.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            
            data.tasks.forEach(task => {
                const taskItem = document.createElement('div');
                taskItem.className = 'task-item';
                
                const taskHeader = document.createElement('div');
                taskHeader.className = 'task-header';
                
                const taskTitle = document.createElement('div');
                taskTitle.className = 'task-title';
                taskTitle.textContent = task.description;
                
                const taskStatus = document.createElement('div');
                taskStatus.className = `task-status status-${task.status}`;
                
                // 翻译任务状态
                let statusText = task.status;
                if (task.status === 'pending') statusText = '进行中';
                else if (task.status === 'completed') statusText = '已完成';
                else if (task.status === 'failed') statusText = '失败';
                
                taskStatus.textContent = statusText;
                
                taskHeader.appendChild(taskTitle);
                taskHeader.appendChild(taskStatus);
                
                const taskInfo = document.createElement('div');
                taskInfo.className = 'task-info';
                taskInfo.textContent = `创建时间: ${new Date(task.created_at).toLocaleString()}`;
                
                taskItem.appendChild(taskHeader);
                taskItem.appendChild(taskInfo);
                
                if (task.result) {
                    const taskResult = document.createElement('div');
                    taskResult.className = 'task-result';
                    
                    // 格式化任务结果 - 添加Markdown支持
                    const formattedResult = formatMarkdown(task.result);
                    taskResult.innerHTML = formattedResult;
                    
                    taskItem.appendChild(taskResult);
                }
                
                taskList.appendChild(taskItem);
            });
        })
        .catch(error => {
            console.error('错误:', error);
            taskList.innerHTML = '<div class="error">加载任务时出错</div>';
        });
    }
    
    // 添加消息到聊天界面
    function addMessageToChat(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        // 滚动到底部
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // 添加已格式化的消息到聊天界面
    function addFormattedMessageToChat(role, formattedContent) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = formattedContent;
        
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        // 滚动到底部
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // 格式化Markdown文本，增强代码块显示
    function formatMarkdown(text) {
        if (!text) return '';
        
        // 临时存储代码块
        let codeBlocks = [];
        let codeBlockId = 0;
        
        // 先提取并保存代码块，用占位符替换
        let formattedWithCodePlaceholders = text.replace(/```(\w*)([\s\S]*?)```/g, function(match, language, code) {
            let placeholder = `__CODE_BLOCK_${codeBlockId}__`;
            codeBlocks.push({
                id: codeBlockId,
                language: language.toLowerCase(),
                code: escapeHtml(code.trim())
            });
            codeBlockId++;
            return placeholder;
        });
        
        // 处理标题格式 (在代码块被提取后)
        formattedWithCodePlaceholders = formattedWithCodePlaceholders.replace(/^(#{1,6})\s+(.*?)(?:\n|$)/gm, function(match, hashes, title) {
            const level = hashes.length;
            return `<h${level} class="markdown-heading">${title}</h${level}>`;
        });
        
        // 处理普通换行
        formattedWithCodePlaceholders = formattedWithCodePlaceholders.replace(/\n/g, '<br>');
        
        // 处理加粗文本
        formattedWithCodePlaceholders = formattedWithCodePlaceholders.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // 处理斜体文本
        formattedWithCodePlaceholders = formattedWithCodePlaceholders.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // 处理段落（确保文本被正确包装）
        formattedWithCodePlaceholders = '<p>' + formattedWithCodePlaceholders.replace(/<br><br>/g, '</p><p>') + '</p>';
        formattedWithCodePlaceholders = formattedWithCodePlaceholders.replace(/<p><h/g, '<h');
        formattedWithCodePlaceholders = formattedWithCodePlaceholders.replace(/<\/h(\d)><\/p>/g, '</h$1>');
        
        // 最后，将代码块占位符替换回格式化的代码块
        let finalFormatted = formattedWithCodePlaceholders;
        for (let block of codeBlocks) {
            finalFormatted = finalFormatted.replace(
                `__CODE_BLOCK_${block.id}__`, 
                `<pre class="code-block ${block.language}"><code>${block.code}</code></pre>`
            );
        }
        
        return finalFormatted;
    }
    
    // HTML字符转义函数
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    // 添加加载指示器
    function addLoadingMessage() {
        const loadingId = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant';
        loadingDiv.id = loadingId;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content loading';
        contentDiv.textContent = '思考中...';
        
        loadingDiv.appendChild(contentDiv);
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return loadingId;
    }
    
    // 移除加载指示器
    function removeLoadingMessage(id) {
        const loadingDiv = document.getElementById(id);
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }
    
    // 清空聊天
    function clearChat() {
        if (confirm('确定要清空聊天记录吗？')) {
            chatMessages.innerHTML = '';
            
            // 调用后端清空记忆
            fetch('/memory/clear', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                console.log('记忆已清空');
            })
            .catch(error => {
                console.error('清空记忆时出错:', error);
            });
        }
    }
    
    // 事件监听器
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    clearChatBtn.addEventListener('click', clearChat);
    
    createTaskBtn.addEventListener('click', createTask);
    taskInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            createTask();
        }
    });
    
    refreshTasksBtn.addEventListener('click', loadTasks);
    
});
```

### 3.`code/templates/index.html`

```html
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>笃小实 - 您的AI助手</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container">
        <header>
            <h1>笃小实</h1>
            <p>您的个人AI助手</p>
        </header>
        
        <div class="tabs">
            <button id="tab-chat" class="tab-btn active">聊天</button>
            <button id="tab-tasks" class="tab-btn">多任务处理</button>
        </div>
        
        <div id="chat-section" class="section active">
            <div id="chat-container">
                <div id="chat-messages">
                    <div class="message assistant">
                        <div class="message-content">
                            你好！我是笃小实，有什么可以帮助您的吗?
                        </div>
                    </div>
                </div>
                
                <div id="chat-input-container">
                    <textarea id="chat-input" placeholder="在此输入您的消息..."></textarea>
                    <button id="send-btn">发送</button>
                    <button id="clear-chat-btn">清空聊天</button>
                </div>
            </div>
        </div>
        
        <div id="tasks-section" class="section">
            <div id="task-container">
                <div id="new-task-container">
                    <textarea id="task-input" placeholder="在此描述您的任务..."></textarea>
                    <button id="create-task-btn">创建任务</button>
                </div>
                
                <div id="task-list-container">
                    <h3>任务列表</h3>
                    <div id="task-list"></div>
                    <button id="refresh-tasks-btn">刷新</button>
                </div>
            </div>
        </div>
    </div>
    
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>
```

## 四、整体（主入口、环境、配置）

### 1.`app.py`

```py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from core.agent import ToyAGI
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')

# 初始化ToyAGI
toyagi = ToyAGI(api_key=os.getenv('DEEPSEEK_API_KEY'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    try:
        data = request.json
        user_message = data.get('message', '')
        if not user_message:
            return jsonify({"error": "未提供消息内容"}), 400
        
        response = toyagi.chat(user_message)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/task', methods=['POST'])
def create_task():
    """创建新任务"""
    try:
        data = request.json
        task_description = data.get('description', '')
        if not task_description:
            return jsonify({"error": "未提供任务描述"}), 400
        
        result = toyagi.process_task(task_description)
        
        # 获取最新任务的详细信息
        tasks = toyagi.get_task_status()
        latest_task = next((t for t in tasks if t["description"] == task_description), None)
        
        return jsonify({
            "result": result,
            "task": latest_task
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tasks', methods=['GET'])
def get_tasks():
    """获取所有任务"""
    try:
        tasks = toyagi.get_task_status()
        return jsonify({"tasks": tasks})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/memory/clear', methods=['POST'])
def clear_memory():
    """清空对话记忆"""
    try:
        toyagi.memory.clear()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # 确保目录存在
    for dir_path in ['static/css', 'static/js', 'templates']:
        os.makedirs(dir_path, exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### 2.`config.py`

```
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 应用配置
DEBUG = True
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
```

### 3.`requirement.txt`

```txt
flask==2.3.3
requests==2.31.0
python-dotenv==1.0.0
```

### 4.`.env`

```env
DEEPSEEK_API_KEY=****
SECRET_KEY=2021012167
```











# ToyAGI-HW2 代码分析

## 一、项目结构

```css
code/
├── app.py              # 主应用入口
├── requirements.txt    # 依赖包列表
├── config.py           # 配置文件
├── readme              # 配置文件
├── core/
    ├── agent.py        # Agent实现
    ├── memory.py       # 上下文记忆功能
    ├── task_manager.py # 任务管理与处理
    └── llm.py          # DeepSeek API接口

```

## 二、整体（主入口、环境、配置）

### 1. `app./py`

```py
# app.py
from flask import Flask, request, jsonify
from core.agent import ToyAGI
import os
from dotenv import load_dotenv

# 加载.env配置
load_dotenv()

# 创建 Flask 应用
app = Flask(__name__)
toyagi = ToyAGI()

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "缺少消息字段"}), 400

    user_input = data["message"]
    try:
        reply = toyagi.chat(user_input)
        return jsonify({"response": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)

```

### 2. config.py

```py
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_URL = "https://madmodel.cs.tsinghua.edu.cn/v1/chat/completions"
# 应用配置
DEBUG = True
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
```

### 3. `chat_in_terminal.py`

```py
import requests

while True:
    msg = input("你：")
    if msg.lower() in ["exit", "quit"]:
        break

    print("")
    res = requests.post("http://localhost:5000/chat", json={"message": msg})
    print("笃小实：", res.json().get("response", res.json().get("error")))
    print("")

```

### 4. `readme`

```
这是作业2的框架代码，你需要将 core\agent.py 和 core\llm.py 中标注了 `TODO` 的地方补全代码。

当然，你也可以自由地修改其他地方的代码。


运行指南如下

1. 安装依赖

    运行 `pip install -r .\requirement.txt`

2. 申请API

    本项目用的清华 deepseek 的 API
    可以在网址：https://madmodel.cs.tsinghua.edu.cn/ 中，右下角“API使用指南”，复制token。（每次登录后，token的有效期为5个小时）


3. 配置API环境文件

    添加`.env`文件
    在文件中输入：
    ```
    DEEPSEEK_API_KEY= your api_keys
    SECRET_KEY= anything if you want (i write my studentNum)
    ```

4. 运行

    在命令行中输入：`python app.py` ，启动端口5000

5. 聊天

    在命令行里输入：`python chat.py`，启动终端聊天窗口

```

### 5. `requirement`

```
flask==2.3.3
requests==2.31.0
python-dotenv==1.0.0
```

## 三、后端实现 `code/core`

### 1. `llm.py`

```py
import requests
import json
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL


class DeepSeekLLM:
    def __init__(self, api_key=None):
        ###############################
        # TODO: 设置 API Key 和 API 地址
        self.api_key = _______
        self.api_url = _______
        ###############################

    def generate_response(self, messages, model="DeepSeek-R1-671B", temperature=0.6,
                          max_tokens=4000, repetition_penalty=1.2, stream=False):
        """
        使用DeepSeek API生成响应

        Args:
            messages: 消息历史列表，格式为[{"role": "user", "content": "..."}, ...]
            model: 使用的模型名称
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成令牌数
            repetition_penalty: 重复惩罚系数
            stream: 是否启用流式传输

        Returns:
            生成的响应文本
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "repetition_penalty": repetition_penalty,
            "stream": stream
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error calling DeepSeek API: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

```

### 2. `memory.py`

```py
class Memory:
    def __init__(self, max_history=10):
        self.conversation_history = []
        self.max_history = max_history
        
    def add_message(self, role, content):
        """添加消息到对话历史"""
        self.conversation_history.append({"role": role, "content": content})
        # 如果历史记录超过最大长度，移除最早的消息
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)
            
    def get_conversation_context(self):
        """获取当前的对话上下文"""
        return self.conversation_history.copy()
    
    def clear(self):
        """清空对话历史"""
        self.conversation_history = []
```

### 3. `agent.py`

```python
from core.llm import DeepSeekLLM
from core.memory import Memory
from core.task_manager import TaskManager
import re

class ToyAGI:
    def __init__(self, api_key=None):
        ################################
        # TODO: 初始化 LLM 和 Memory 和 TaskManager
        self.llm = _______
        self.memory = _______
        self.task_manager = _______
        ################################

        ###############################
        # TODO: 设置系统提示
        self.system_prompt = (
            # 系统提示词的内容
            # 例如：
            # "你是笃小实，一个有帮助的、自主的AI助手。"
            # "你可以处理任务、维持对话，并帮助用户解决各种需求。"
            # "请始终保持有帮助、准确和友好的态度。"
        )
        ###############################

    def chat(self, user_message):
        """处理用户消息并返回响应"""
        ################################
        # TODO: 添加用户消息到记忆
        self.memory.add_message("user", _______)
        ################################

        # 准备发送给LLM的上下文
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.memory.get_conversation_context())

        ################################
        # TODO: 根据消息，获取LLM响应
        response = self.llm.generate_response(_______)
        ################################

        # 添加助手响应到记忆
        self.memory.add_message("assistant", response)

        return response

    def process_task(self, task_description):
        """处理一个任务"""
        task = self.task_manager.add_task(task_description)

        # 增强系统提示，要求返回格式化代码
        enhanced_system_prompt = (
            f"{self.system_prompt}\n\n"
            "在你的回答中提供代码时，请遵循以下格式指南：\n"
            "1. 始终将代码放在带有适当语言标签的markdown代码块内。\n"
            "2. 对于Python代码，在开始处使用```python，在结束处使用```。\n"
            "3. 用适当的缩进和换行来格式化代码，使其易于阅读。\n"
            "4. 添加注释来解释代码中的复杂部分。\n"
            "5. 在适当的情况下将长代码行分成多行。"
        )

        # 构建任务提示
        task_prompt = f"请完成以下任务: {task_description}"
        messages = [
            {"role": "system", "content": enhanced_system_prompt},
            {"role": "user", "content": task_prompt}
        ]

        try:
            # 获取LLM对任务的处理结果
            result = self.llm.generate_response(messages)

            # 检测是否包含Python代码，如果没有明确的Markdown格式，添加格式
            if "```python" not in result and self._looks_like_python_code(result):
                result = "```python\n" + result + "\n```"

            task.mark_completed(result)
            return result
        except Exception as e:
            task.mark_failed(str(e))
            return f"任务处理失败: {str(e)}"

    def _looks_like_python_code(self, text):
        """判断文本是否可能是未格式化的Python代码"""
        python_indicators = [
            "import ", "from ", "def ", "class ",
            "if __name__", "print(", "return ",
            "for ", "while ", "try:", "except:"
        ]

        # 检查文本中是否包含Python代码特征
        for indicator in python_indicators:
            if indicator in text:
                return True

        # 检查是否有多行代码结构
        lines = text.split('\n')
        indent_pattern = r'^\s{2,}'
        indented_lines = 0

        for line in lines:
            if line.strip() and re.match(indent_pattern, line):
                indented_lines += 1

        # 如果有多个缩进行，可能是Python代码
        if indented_lines >= 3:
            return True

        return False

    def get_task_status(self):
        """获取所有任务的状态"""
        return [task.to_dict() for task in self.task_manager.get_all_tasks()]

```

### 4. `task_manager.py`

```py
import re
from datetime import datetime

class Task:
    def __init__(self, id, description):
        self.id = id
        self.description = description
        self.status = "pending"
        self.result = None
        self.created_at = datetime.now()
        self.completed_at = None
        self.failed_at = None
        self.error = None
        
    def mark_completed(self, result=None):
        """标记任务为已完成"""
        self.status = "completed"
        self.completed_at = datetime.now()
        self.result = result
        
    def mark_failed(self, error=None):
        """标记任务为失败"""
        self.status = "failed"
        self.failed_at = datetime.now()
        self.error = error
        
    def to_dict(self):
        """转换为字典表示"""
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "error": self.error
        }
        
class TaskManager:
    def __init__(self):
        self.tasks = []
        self.next_id = 1
        
    def add_task(self, description):
        """添加新任务"""
        task = Task(self.next_id, description)
        self.tasks.append(task)
        self.next_id += 1
        return task
        
    def get_task(self, task_id):
        """获取指定ID的任务"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
        
    def get_all_tasks(self):
        """获取所有任务"""
        return self.tasks
```

