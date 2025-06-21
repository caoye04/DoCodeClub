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