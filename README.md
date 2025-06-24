# Coze2API

Coze2API 是一个轻量级、高性能的适配器，基于 FastAPI 构建。它能将 [Coze API](https://www.coze.cn/) 的响应无缝转换为 OpenAI Chat Completions API 的标准流式（SSE）格式。

通过本项目，你可以将任何兼容 OpenAI API 的客户端或应用，直接对接到你的 Coze Bot。

## ✨ 特性

  - **兼容 OpenAI 接口**: 提供 `v1/chat/completions` 接口，完全兼容 OpenAI API 规范。
  - **实时流式转换**: 将 Coze 的响应数据实时转换为 OpenAI SSE 格式，实现流式效果。
  - **灵活的安全认证**: 通过 API 密钥保护你的服务，并支持自定义 HTTP 头。
  - **健康状态监控**: 内置 `/health` 健康检查接口，便于系统集成和监控。
  - **高可配置性**: 所有关键参数均可通过环境变量设置。

## 🚀 快速开始

### 1\. 克隆仓库

```bash
git clone https://github.com/Mahiruchan/coze2api.git
cd coze2api
```

### 2\. 配置环境变量

在项目根目录创建一个 `.env` 文件，并填入你的配置。

```ini
# .env 文件示例

# Coze Bot 配置
COZE_BOT_ID=your_bot_id
COZE_API_TOKEN=your_api_token # 你的 Coze 访问令牌 (PAT)

# 服务配置
COZE_API_BASE=https://api.coze.cn       # Coze API 地址
API_KEY_HEADER_NAME=X-API-Key           # 客户端访问时使用的密钥Header
VALID_API_KEYS='["key1", "key2"]'       # 定义一组有效的API密钥
HTTPX_TIMEOUT=60                        # 请求上游API的超时时间（秒）
LOG_LEVEL=INFO                          # 日志级别
PORT=8080                               # 服务监听端口
```

### 3\. 安装依赖

```bash
pip install -r requirements.txt
```

### 4\. 运行服务

```bash
python main.py
```

服务将默认在 `http://0.0.0.0:8080` 启动。

## 📖 API 文档

### `POST /v1/chat/completions`

此端点接收符合 OpenAI 格式的聊天请求，并以 Server-Sent Events (SSE) 格式返回流式响应。

**安全**: 此请求需要通过 API 密钥进行认证。

#### 请求示例 (`curl`)

```bash
curl -X POST http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: key1" \
  -d '{
    "model": "coze-model",
    "user": "test-user",
    "messages": [
      {
        "role": "user",
        "content": "你好，请介绍一下你自己。"
      }
    ],
    "stream": true
  }'
```

## 🔐 安全性

API 访问由 API 密钥保护。客户端必须在 HTTP 请求头中提供有效的密钥。

  - **Header 名称**: 由环境变量 `API_KEY_HEADER_NAME` 定义 (默认为 `X-API-Key`)。
  - **有效密钥**: 在 `.env` 文件的 `VALID_API_KEYS` 变量中定义。

如果密钥缺失或无效，服务将返回 `403 Forbidden` 状态码。

## 🤝 贡献

欢迎任何形式的贡献！

## 📄 许可证

该项目基于 [MIT 许可证](https://www.google.com/search?q=LICENSE) 发布。
