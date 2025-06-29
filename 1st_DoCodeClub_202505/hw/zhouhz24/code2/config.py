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