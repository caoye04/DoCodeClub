from core.llm import DeepSeekLLM
from core.memory import Memory
from core.task_manager import TaskManager
import re

class ToyAGI:
    def __init__(self, api_key=None):
        ################################
        # TODO: 初始化 LLM 和 Memory 和 TaskManager
        self.llm = DeepSeekLLM(api_key)
        self.memory = Memory(10)
        self.task_manager = TaskManager()
        ################################

        ###############################
        # TODO: 设置系统提示
        self.system_prompt = (
            # 系统提示词的内容
            # 例如：
            "你是笃小实，一个有帮助的、自主的AI助手。"
            "你可以处理任务、维持对话，并帮助用户解决各种需求。"
            "请始终保持有帮助、准确和友好的态度。"
        )
        ###############################

    def chat(self, user_message):
        """处理用户消息并返回响应"""
        ################################
        # TODO: 添加用户消息到记忆
        self.memory.add_message("user", user_message)
        ################################

        # 准备发送给LLM的上下文
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.memory.get_conversation_context())

        ################################
        # TODO: 根据消息，获取LLM响应
        response = self.llm.generate_response(messages)
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
