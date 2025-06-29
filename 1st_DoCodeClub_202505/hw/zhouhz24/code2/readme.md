这是停云的项目文件夹

运行指南如下

1. 安装依赖

    运行 `pip install -r .\requirement.txt`

2. 申请API

    本项目用的清华 deepseek 的 API
    可以在网址：https://madmodel.cs.tsinghua.edu.cn/ 中，右下角“API使用指南”，复制token。（每次登录后，token的有效期为5个小时）


3. 配置API环境文件

    添加`.env`文件
    在文件中输入：
    ```
    DEEPSEEK_API_KEY= your api_keys
    SECRET_KEY= anything if you want (i write my studentNum)
    ```

4. 运行

    在命令行中输入：`python app.py` ，启动端口5000

5. 聊天

    在命令行里输入：`python chat.py`，启动终端聊天窗口
