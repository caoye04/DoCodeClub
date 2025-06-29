import requests
import json
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL


class DeepSeekLLM:
    def __init__(self, api_key=None):
        ###############################
        # TODO: 设置 API Key 和 API 地址
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.api_url = DEEPSEEK_API_URL
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
