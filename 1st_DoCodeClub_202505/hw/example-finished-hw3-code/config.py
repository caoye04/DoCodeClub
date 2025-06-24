import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 如果使用清华镜像，取消注释下一行
<<<<<<< HEAD
#DEEPSEEK_API_URL = "https://madmodel.cs.tsinghua.edu.cn/v1/chat/completions"
=======
DEEPSEEK_API_URL = "https://madmodel.cs.tsinghua.edu.cn/v1/chat/completions"
>>>>>>> 4ab59cfa9ae65fee9f94c4d8e1f7eaf9d4fbbf05

# 应用配置
DEBUG = True
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-2025")

# 聊天配置
MAX_CONVERSATION_HISTORY = 10
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TEMPERATURE = 0.7
MAX_TOKENS = 4000