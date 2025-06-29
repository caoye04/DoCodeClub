document.addEventListener('DOMContentLoaded', function() {
    // DOM元素获取
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
    const loadingOverlay = document.getElementById('loading-overlay');
    
    // 应用状态
    let isProcessing = false;
    
    // 标签页切换
    tabChat.addEventListener('click', function() {
        switchTab('chat');
    });
    
    tabTasks.addEventListener('click', function() {
        switchTab('tasks');
        loadTasks(); // 切换到任务标签时加载任务
    });
    
    function switchTab(tab) {
        if (tab === 'chat') {
            tabChat.classList.add('active');
            tabTasks.classList.remove('active');
            chatSection.classList.add('active');
            tasksSection.classList.remove('active');
        } else {
            tabChat.classList.remove('active');
            tabTasks.classList.add('active');
            chatSection.classList.remove('active');
            tasksSection.classList.add('active');
        }
    }
    
    // 发送聊天消息
    function sendMessage() {
        if (isProcessing) return;
        
        const message = chatInput.value.trim();
        if (!message) {
            showToast('请输入消息内容', 'warning');
            return;
        }
        
        // 检查消息长度
        if (message.length > 2000) {
            showToast('消息长度不能超过2000个字符', 'error');
            return;
        }
        
        isProcessing = true;
        sendBtn.disabled = true;
        sendBtn.textContent = '发送中...';
        
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
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            removeLoadingMessage(loadingId);
            
            if (data.response) {
                // 格式化响应内容
                const formattedResponse = formatMarkdown(data.response);
                addFormattedMessageToChat('assistant', formattedResponse);
                showToast('消息发送成功', 'success');
            } else if (data.error) {
                addMessageToChat('assistant', `❌ 错误: ${data.error}`);
                showToast('服务器返回错误', 'error');
            }
        })
        .catch(error => {
            console.error('发送消息错误:', error);
            removeLoadingMessage(loadingId);
            addMessageToChat('assistant', `❌ 抱歉，出现了问题: ${error.message}`);
            showToast('发送消息失败，请重试', 'error');
        })
        .finally(() => {
            isProcessing = false;
            sendBtn.disabled = false;
            sendBtn.textContent = '发送';
        });
    }
    
    // 创建任务
    function createTask() {
        if (isProcessing) return;
        
        const description = taskInput.value.trim();
        if (!description) {
            showToast('请输入任务描述', 'warning');
            return;
        }
        
        if (description.length > 1000) {
            showToast('任务描述长度不能超过1000个字符', 'error');
            return;
        }
        
        isProcessing = true;
        createTaskBtn.disabled = true;
        createTaskBtn.textContent = '创建中...';
        
        taskInput.value = '';
        showLoading();
        
        // 发送任务到后端
        fetch('/task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ description: description })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            hideLoading();
            if (data.result) {
                showToast('任务创建成功', 'success');
                loadTasks(); // 刷新任务列表
            } else if (data.error) {
                showToast(`任务创建失败: ${data.error}`, 'error');
            }
        })
        .catch(error => {
            console.error('创建任务错误:', error);
            hideLoading();
            showToast(`创建任务失败: ${error.message}`, 'error');
        })
        .finally(() => {
            isProcessing = false;
            createTaskBtn.disabled = false;
            createTaskBtn.textContent = '创建任务';
        });
    }
    
    // 加载任务列表
    function loadTasks() {
        taskList.innerHTML = '<div class="loading-message">⏳ 正在加载任务...</div>';
        
        fetch('/tasks')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            taskList.innerHTML = '';
            
            if (!data.tasks || data.tasks.length === 0) {
                taskList.innerHTML = '<div class="no-tasks">📝 暂无任务，请创建第一个任务</div>';
                return;
            }
            
            // 按创建时间倒序排序
            data.tasks.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            
            data.tasks.forEach(task => {
                const taskItem = createTaskElement(task);
                taskList.appendChild(taskItem);
            });
        })
        .catch(error => {
            console.error('加载任务错误:', error);
            taskList.innerHTML = `<div class="no-tasks">❌ 加载任务失败: ${error.message}</div>`;
        });
    }
    
    // 创建任务元素
    function createTaskElement(task) {
        const taskItem = document.createElement('div');
        taskItem.className = 'task-item';
        
        const taskHeader = document.createElement('div');
        taskHeader.className = 'task-header-item';
        
        const taskTitle = document.createElement('div');
        taskTitle.className = 'task-title';
        taskTitle.textContent = task.description;
        
        const taskStatus = document.createElement('div');
        taskStatus.className = `task-status status-${task.status}`;
        
        // 翻译任务状态
        const statusMap = {
            'pending': '⏳ 进行中',
            'completed': '✅ 已完成',
            'failed': '❌ 失败'
        };
        taskStatus.textContent = statusMap[task.status] || task.status;
        
        taskHeader.appendChild(taskTitle);
        taskHeader.appendChild(taskStatus);
        
        const taskInfo = document.createElement('div');
        taskInfo.className = 'task-info';
        const createTime = new Date(task.created_at).toLocaleString('zh-CN');
        taskInfo.textContent = `📅 创建时间: ${createTime}`;
        
        taskItem.appendChild(taskHeader);
        taskItem.appendChild(taskInfo);
        
        if (task.result) {
            const taskResult = document.createElement('div');
            taskResult.className = 'task-result';
            
            // 格式化任务结果
            const formattedResult = formatMarkdown(task.result);
            taskResult.innerHTML = formattedResult;
            
            taskItem.appendChild(taskResult);
        }
        
        if (task.error) {
            const taskError = document.createElement('div');
            taskError.className = 'task-result';
            taskError.style.borderLeftColor = '#e74c3c';
            taskError.style.background = '#fdf2f2';
            taskError.textContent = `错误: ${task.error}`;
            
            taskItem.appendChild(taskError);
        }
        
        return taskItem;
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
        scrollToBottom();
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
        scrollToBottom();
    }
    
    // 格式化Markdown文本
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
        
        // 处理标题格式
        formattedWithCodePlaceholders = formattedWithCodePlaceholders.replace(/^(#{1,6})\s+(.*?)(?:\n|$)/gm, function(match, hashes, title) {
            const level = hashes.length;
            return `<h${level} style="margin: 15px 0 10px 0; color: #2c3e50; font-weight: 600;">${escapeHtml(title)}</h${level}>`;
        });
        
        // 处理换行
        formattedWithCodePlaceholders = formattedWithCodePlaceholders.replace(/\n/g, '<br>');
        
        // 处理加粗文本
        formattedWithCodePlaceholders = formattedWithCodePlaceholders.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // 处理斜体文本
        formattedWithCodePlaceholders = formattedWithCodePlaceholders.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // 处理列表
        formattedWithCodePlaceholders = formattedWithCodePlaceholders.replace(/^[\*\-]\s+(.*?)(?:<br>|$)/gm, '<li style="margin-left: 20px;">$1</li>');
        formattedWithCodePlaceholders = formattedWithCodePlaceholders.replace(/(<li.*?<\/li>)/g, '<ul style="margin: 10px 0;">$1</ul>');
        
        // 最后，将代码块占位符替换回格式化的代码块
        let finalFormatted = formattedWithCodePlaceholders;
        for (let block of codeBlocks) {
            const codeHtml = `<pre class="code-block"><code>${block.code}</code></pre>`;
            finalFormatted = finalFormatted.replace(`__CODE_BLOCK_${block.id}__`, codeHtml);
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
        contentDiv.className = 'message-content loading-message';
        contentDiv.innerHTML = '🤔 思考中<span class="dots">...</span>';
        
        loadingDiv.appendChild(contentDiv);
        chatMessages.appendChild(loadingDiv);
        scrollToBottom();
        
        // 添加跳动效果
        let dotCount = 0;
        const loadingInterval = setInterval(() => {
            const dotsSpan = contentDiv.querySelector('.dots');
            if (dotsSpan) {
                dotCount = (dotCount + 1) % 4;
                dotsSpan.textContent = '.'.repeat(dotCount);
            } else {
                clearInterval(loadingInterval);
            }
        }, 500);
        
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
        if (isProcessing) return;
        
        if (confirm('🗑️ 确定要清空聊天记录吗？此操作不可撤销。')) {
            chatMessages.innerHTML = '';
            
            // 添加默认欢迎消息
            addMessageToChat('assistant', '你好！我是笃小实，有什么可以帮助您的吗? 🌟');
            
            // 调用后端清空记忆
            fetch('/memory/clear', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                console.log('记忆已清空');
                showToast('聊天记录已清空', 'success');
            })
            .catch(error => {
                console.error('清空记忆时出错:', error);
                showToast('清空记忆时出错', 'error');
            });
        }
    }
    
    // 滚动到底部
    function scrollToBottom() {
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 100);
    }
    
    // 显示/隐藏加载覆盖层
    function showLoading() {
        loadingOverlay.classList.remove('hidden');
    }
    
    function hideLoading() {
        loadingOverlay.classList.add('hidden');
    }
    
    // 显示提示消息
    function showToast(message, type = 'info') {
        // 创建提示元素
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 10000;
            animation: slideInRight 0.3s ease;
            max-width: 300px;
            word-wrap: break-word;
        `;
        
        // 根据类型设置颜色
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8'
        };
        toast.style.backgroundColor = colors[type] || colors.info;
        
        // 设置消息内容
        toast.textContent = message;
        
        // 添加到页面
        document.body.appendChild(toast);
        
        // 3秒后自动移除
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 300);
        }, 3000);
        
        // 点击关闭
        toast.addEventListener('click', () => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 300);
        });
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
    
    // 页面加载完成后的初始化
    console.log('🚀 ToyAGI Web应用已启动');
    showToast('欢迎使用ToyAGI！', 'success');
    
    // 添加动画样式
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
});