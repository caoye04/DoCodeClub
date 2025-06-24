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

#交作业