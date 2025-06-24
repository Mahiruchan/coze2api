# Coze2API

这是一个基于 FastAPI 的适配器，用于将 Coze API 的响应转换为 OpenAI SSE 格式。该适配器处理与 Coze bot 的交互，并以流式方式返回符合 OpenAI API 格式的数据。

## 特性

* **聊天 API 接口**: 将用户输入流式地转发到 Coze API，并将其响应转换为 OpenAI SSE 格式。
* **API 密钥安全**: 只允许有效的 API 密钥进行请求。
* **健康检查接口**: 提供简单的健康检查，监控服务状态。
* **兼容 OpenAI SSE 格式**: 将 Coze API 的流式响应格式化为符合 OpenAI SSE 格式。

## 需求

* Python 3.8+
* 安装项目依赖的 Python 库（通过 `pip install -r requirements.txt` 安装）。

## 安装

### 克隆仓库

```bash
git clone https://github.com/Mahiruchan/coze2api.git
cd coze2api
```

### 配置环境变量

在项目根目录创建一个 `.env` 文件，并添加以下变量：

```ini
COZE_BOT_ID=your_bot_id
COZE_API_TOKEN=your_api_token #临时Token或者PAT
COZE_API_BASE=https://api.coze.cn  # 默认 Coze API 基础 URL
API_KEY_HEADER_NAME=X-API-Key  # API 密钥的 HTTP 头部名称
VALID_API_KEYS=["key1", "key2"]  # 有效 API 密钥列表
HTTPX_TIMEOUT=60  # HTTPX 请求的超时时间
LOG_LEVEL=INFO  # 日志级别
```

### 安装依赖

运行以下命令来安装所需的 Python 依赖：

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
python main.py
```

应用默认会在 `http://0.0.0.0:8000` 启动。

## API 接口

### **POST /v1/chat/completions**

将用户的消息发送到 Coze API，获取响应，并将其转换为 OpenAI Chat API 所需的流式 SSE 格式响应。

### 示例 curl 请求

```bash
curl -X POST http://127.0.0.1:8080/v1/chat/completions \
-H "Content-Type: application/json" \
-H "X-API-Key: key1" \
-d '{
  "model": "coze-model",
  "user": "test-user",
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "stream": true
}'
```

## 安全性

API 访问通过 API 密钥进行保护。有效的 API 密钥在 `.env` 文件中的 `VALID_API_KEYS` 变量中定义。

请求 `/v1/chat/completions` 接口时，需要在请求头中包含 API 密钥：

如果 API 密钥无效或缺失，服务器将返回 `403 Forbidden` 状态码。


## 贡献

如果你想为此项目贡献代码，请 fork 仓库并提交一个 pull request，欢迎你的修改和建议！

## 许可证

该项目使用 MIT 许可证。详情请查看 [LICENSE](LICENSE) 文件。
