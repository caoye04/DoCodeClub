from flask import Flask, render_template, request, jsonify
from core.agent import ToyAGI
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key')

# 初始化ToyAGI
toyagi = ToyAGI(api_key=os.getenv('DEEPSEEK_API_KEY'))

# TODO1：完成主页路由
# 提示：使用@app.route装饰器定义根路径'/'，函数名为index，返回render_template('index.html')
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    try:
        data = request.json
        user_message = data.get('message', '')
        if not user_message:
            return jsonify({"error": "未提供消息内容"}), 400
        
        # TODO2：调用toyagi处理用户消息
        # 提示：使用toyagi.chat()方法处理user_message
        response = toyagi.chat(user_message)
        return jsonify({"response": response})
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/task', methods=['POST'])
def create_task():
    """创建新任务"""
    try:
        data = request.json
        task_description = data.get('description', '')
        if not task_description:
            return jsonify({"error": "未提供任务描述"}), 400
        
        result = toyagi.process_task(task_description)
        
        # 获取最新任务的详细信息
        tasks = toyagi.get_task_status()
        latest_task = next((t for t in tasks if t["description"] == task_description), None)
        
        return jsonify({
            "result": result,
            "task": latest_task
        })
    except Exception as e:
        print(f"Task error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/tasks', methods=['GET'])
def get_tasks():
    """获取所有任务"""
    try:
        tasks = toyagi.get_task_status()
        return jsonify({"tasks": tasks})
    except Exception as e:
        print(f"Get tasks error: {e}")
        return jsonify({"error": str(e)}), 500

# TODO3：完成清空记忆的路由
# 提示：路径为'/memory/clear'，方法为['POST']
@app.route('/memory/clear', methods=['POST'])
def clear_memory():
    """清空对话记忆"""
    try:
        toyagi.memory.clear()
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Clear memory error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({"status": "healthy", "message": "ToyAGI is running"})

if __name__ == '__main__':
    # 确保目录存在
    for dir_path in ['static/css', 'static/js', 'templates', 'core']:
        os.makedirs(dir_path, exist_ok=True)
    
    print("启动ToyAGI Web服务...")
    print("访问地址: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)