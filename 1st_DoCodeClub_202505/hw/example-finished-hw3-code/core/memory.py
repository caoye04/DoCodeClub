from config import MAX_CONVERSATION_HISTORY

class Memory:
    def __init__(self, max_history=None):
        self.conversation_history = []
        self.max_history = max_history or MAX_CONVERSATION_HISTORY
        
    def add_message(self, role, content):
        """添加消息到对话历史"""
        if not content or not content.strip():
            return
            
        self.conversation_history.append({"role": role, "content": content.strip()})
        
        # 如果历史记录超过最大长度，移除最早的消息（保留系统消息）
        while len(self.conversation_history) > self.max_history:
            # 找到第一个非系统消息并移除
            for i, msg in enumerate(self.conversation_history):
                if msg["role"] != "system":
                    self.conversation_history.pop(i)
                    break
            else:
                # 如果全是系统消息，移除最早的
                self.conversation_history.pop(0)
            
    def get_conversation_context(self):
        """获取当前的对话上下文"""
        return self.conversation_history.copy()
    
    def clear(self):
        """清空对话历史"""
        self.conversation_history = []
        print("对话记忆已清空")
        
    def get_message_count(self):
        """获取消息数量"""
        return len(self.conversation_history)
        
    def get_last_message(self):
        """获取最后一条消息"""
        if self.conversation_history:
            return self.conversation_history[-1]
        return None