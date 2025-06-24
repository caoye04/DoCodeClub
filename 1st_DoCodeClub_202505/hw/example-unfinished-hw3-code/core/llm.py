import requests
import json
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL

class DeepSeekLLM:
    def __init__(self, api_key=None):
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.api_url = DEEPSEEK_API_URL
        
        if not self.api_key:
            raise ValueError("DeepSeek API key is required")
        
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
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            print(f"Sending request to {self.api_url}")
            response = requests.post(self.api_url, headers=headers, data=json.dumps(payload), timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "抱歉，我现在无法处理您的请求。"
                
        except requests.exceptions.Timeout:
            print("Request timeout")
            return "请求超时，请稍后重试。"
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return f"网络请求错误：{str(e)}"
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return "响应格式错误，请重试。"
        except Exception as e:
            print(f"Unexpected error calling DeepSeek API: {e}")
            return f"抱歉，发生了未知错误：{str(e)}"