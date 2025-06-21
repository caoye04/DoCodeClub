# ToyAGI-HW3 Web版AI助手

一个基于Flask和DeepSeek API的Web版AI对话助手，支持聊天对话和任务处理功能。

## ✨ 功能特性

- 🗨️ **智能对话**: 与AI进行自然语言对话
- 📋 **任务处理**: 创建和管理AI任务
- 💾 **记忆管理**: 维护对话上下文记忆
- 🎨 **美观界面**: 现代化的响应式Web界面
- 📱 **移动适配**: 支持手机和平板设备
- ⚡ **实时交互**: 流畅的前后端数据交互

## 🛠️ 技术栈

**后端**:
- Python 3.7+
- Flask 2.3.3
- DeepSeek API
- python-dotenv

**前端**:
- HTML5
- CSS3 (Flexbox, Grid, 动画)
- Vanilla JavaScript (ES6+)
- Fetch API

## 📦 安装指南

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 文件为 `.env`:

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的配置:

```.env
DEEPSEEK_API_KEY=your_actual_api_key_here
SECRET_KEY=your_secret_key_here
```

### 3. 获取DeepSeek API Key

#### 方法一：官方API (推荐)

1. 访问 [DeepSeek官网](https://www.deepseek.com/)
2. 注册账号并获取API Key
3. 将API Key填入 `.env` 文件

#### 方法二：清华镜像 (学生用户)

1. 访问 [清华DeepSeek镜像](https://madmodel.cs.tsinghua.edu.cn/)
2. 右下角"API使用指南"获取token
3. 在 `config.py` 中取消注释清华镜像URL
4. 将token填入 `.env` 文件

## 🚀 运行应用

```py
python app.py
```

应用将在 `http://localhost:5000` 启动

## 🎯 使用说明

### 聊天功能

1. 打开浏览器访问 `http://localhost:5000`
2. 在输入框中输入消息
3. 点击"发送"按钮或按回车键发送
4. AI将实时回复你的消息
5. 使用"清空聊天"按钮清除对话历史

### 任务处理

1. 点击"任务处理"标签页
2. 在文本框中描述你的任务
3. 点击"创建任务"按钮
4. 查看任务执行结果
5. 使用"刷新"按钮更新任务列表

### 快捷键

- `Enter`: 发送消息/创建任务
- `Shift + Enter`: 在输入框中换行

## 📁 项目结构

```mipsasm
toyagi-hw3/
├── app.py                 # Flask应用主文件
├── config.py             # 配置文件
├── requirements.txt      # Python依赖
├── README.md            # 项目说明
├── .env.example         # 环境变量模板
├── core/                # 后端核心模块
│   ├── __init__.py
│   ├── agent.py         # AI代理
│   ├── llm.py          # 语言模型接口
│   ├── memory.py       # 记忆管理
│   └── task_manager.py # 任务管理
├── templates/           # HTML模板
│   └── index.html
└── static/             # 静态文件
    ├── css/
    │   └── style.css   # 样式文件
    └── js/
        └── main.js     # JavaScript逻辑
```

## 🔧 配置说明

### config.py 主要配置项

```config.py
# API配置
DEEPSEEK_API_KEY = "your-api-key"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 应用配置
MAX_CONVERSATION_HISTORY = 10  # 最大对话历史数
DEFAULT_TEMPERATURE = 0.7      # AI创造性参数
MAX_TOKENS = 4000             # 最大回复长度
```

## 🐛 故障排除

### 常见问题

**1. API Key错误**

```
Error: DeepSeek API key is required
```

解决方案: 检查 `.env` 文件中的API Key是否正确设置

**2. 网络连接超时**

```
请求超时，请稍后重试
```

解决方案: 检查网络连接，或尝试使用清华镜像

**3. 端口被占用**

```
Address already in use
```

解决方案: 更改端口或终止占用进程

```
# 查找占用端口的进程
lsof -i :5000

# 终止进程
kill -9 <PID>
```

**4. 模块导入错误**

```
ModuleNotFoundError: No module named 'flask'
```

解决方案: 确保安装依赖

```
pip install -r requirements.txt
```

### 
