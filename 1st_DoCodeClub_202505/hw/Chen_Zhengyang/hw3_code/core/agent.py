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
            "你是笃小实，一个有帮助的、智能的AI助手。"
            "你可以进行自然对话、回答问题、处理任务，并帮助用户解决各种需求。"
            "请始终保持有帮助、准确、友好和专业的态度。"
            "在回答时要简洁明了，但也要确保信息的完整性。"
        )
        print("ToyAGI初始化完成")
        
    def chat(self, user_message):
        """处理用户消息并返回响应"""
        if not user_message or not user_message.strip():
            return "请输入有效的消息内容。"
            
        # 添加用户消息到记忆
        self.memory.add_message("user", user_message)
        
        # 准备发送给LLM的上下文
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.memory.get_conversation_context())
        
        # 获取LLM响应
        response = self.llm.generate_response(messages)
        
        # 添加助手响应到记忆
        self.memory.add_message("assistant", response)
        
        print(f"用户: {user_message}")
        print(f"笃小实: {response}")
        
        return response
    
    def process_task(self, task_description):
        """处理一个任务"""
        if not task_description or not task_description.strip():
            return "请提供有效的任务描述。"
            
        task = self.task_manager.add_task(task_description)
        
        # 增强系统提示，要求返回格式化内容
        enhanced_system_prompt = (
            f"{self.system_prompt}\n\n"
            "你现在需要处理一个具体的任务。请按照以下要求：\n"
            "1. 仔细理解任务需求\n"
            "2. 提供详细和有用的解决方案\n"
            "3. 如果涉及代码，请用适当的markdown代码块格式化\n"
            "4. 确保回答的实用性和可操作性\n"
            "5. 如果任务不清楚，请询问具体细节"
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
            
            # 检测是否包含代码，如果没有明确的格式，尝试添加格式
            if self._looks_like_code(result) and "```" not in result:
                # 尝试识别代码语言
                language = self._detect_code_language(result)
                result = f"```{language}\n{result}\n```"
                
            task.mark_completed(result)
            return result
        except Exception as e:
            error_msg = f"任务处理失败: {str(e)}"
            task.mark_failed(error_msg)
            return error_msg
    
    def _looks_like_code(self, text):
        """判断文本是否可能是代码"""
        code_indicators = [
            "def ", "class ", "import ", "from ",
            "function ", "var ", "let ", "const ",
            "public ", "private ", "protected ",
            "if (", "for (", "while (", "switch (",
            "<?php", "<html", "<script", "SELECT ", "CREATE "
        ]
        
        # 检查文本中是否包含代码特征
        text_lower = text.lower()
        for indicator in code_indicators:
            if indicator.lower() in text_lower:
                return True
                
        # 检查是否有多行缩进结构
        lines = text.split('\n')
        indent_pattern = r'^\s{2,}'
        indented_lines = sum(1 for line in lines if line.strip() and re.match(indent_pattern, line))
        
        return indented_lines >= 3
    
    def _detect_code_language(self, text):
        """尝试检测代码语言"""
        text_lower = text.lower()
        
        # Python特征
        if any(keyword in text_lower for keyword in ["def ", "import ", "from ", "print(", "__init__"]):
            return "python"
        
        # JavaScript特征
        if any(keyword in text_lower for keyword in ["function ", "var ", "let ", "const ", "console.log"]):
            return "javascript"
        
        # HTML特征
        if any(keyword in text_lower for keyword in ["<html", "<div", "<script", "<!doctype"]):
            return "html"
        
        # CSS特征
        if any(keyword in text_lower for keyword in ["background-color", "font-size", "margin:", "padding:"]):
            return "css"
        
        # SQL特征
        if any(keyword in text_lower for keyword in ["select ", "create ", "insert ", "update ", "delete "]):
            return "sql"
        
        return ""  # 未知语言
    
    def get_task_status(self):
        """获取所有任务的状态"""
        return [task.to_dict() for task in self.task_manager.get_all_tasks()]
    
    def get_conversation_summary(self):
        """获取对话摘要信息"""
        return {
            "message_count": self.memory.get_message_count(),
            "task_count": len(self.task_manager.get_all_tasks()),
            "pending_tasks": len(self.task_manager.get_pending_tasks()),
            "completed_tasks": len(self.task_manager.get_completed_tasks())
        }