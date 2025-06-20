import os
import sys
import time
import json
import logging
from functools import lru_cache

import httpx
from fastapi import FastAPI, Request, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader, APIKey
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsError
from dotenv import load_dotenv

# === .env 示例 ===
# COZE_BOT_ID=your_bot_id
# COZE_API_TOKEN=your_api_token
# VALID_API_KEYS=["key1","key2"]
# API_KEY_HEADER_NAME=X-API-Key
# HTTPX_TIMEOUT=60
# LOG_LEVEL=INFO

# --- 加载环境变量 ---
load_dotenv()

# --- 配置管理 ---
class Settings(BaseSettings):
    coze_bot_id: str = Field(..., env="COZE_BOT_ID")
    coze_api_token: str = Field(..., env="COZE_API_TOKEN")
    coze_api_base: str = Field("https://api.coze.cn", env="COZE_API_BASE")
    api_key_header_name: str = Field("X-API-Key", env="API_KEY_HEADER_NAME")
    valid_api_keys: list[str] = Field([], env="VALID_API_KEYS")
    timeout_seconds: int = Field(60, env="HTTPX_TIMEOUT")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    try:
        return Settings()
    except SettingsError as e:
        sys.stderr.write(f"Environment configuration error: {e}\n")
        sys.exit(1)

settings = get_settings()

# --- 日志配置 ---
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("chat_service")

# --- FastAPI 应用 ---
async def lifespan(app: FastAPI):
    # 启动时创建 HTTPX AsyncClient
    timeout = httpx.Timeout(settings.timeout_seconds)
    app.state.httpx_client = httpx.AsyncClient(timeout=timeout)
    logger.info("HTTPX AsyncClient initialized with timeout %s seconds", settings.timeout_seconds)
    yield
    # 关闭时清理
    await app.state.httpx_client.aclose()
    logger.info("HTTPX AsyncClient closed")

app = FastAPI(
    title="Coze2OpenAI Adapter",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# --- Pydantic 请求模型 ---
class Message(BaseModel):
    role: str
    content: str

class ChatPayload(BaseModel):
    model: str = Field("coze-model")
    user: str = Field("default_user")
    messages: list[Message]
    stream: bool = Field(True)

# --- API Key 安全依赖 ---
api_key_header = APIKeyHeader(name=settings.api_key_header_name, auto_error=False)
async def get_api_key(api_key: str = Security(api_key_header)) -> str:
    if api_key in settings.valid_api_keys:
        return api_key
    logger.warning("Unauthorized access with API Key: %s", api_key)
    raise HTTPException(status_code=403, detail="Invalid API Key")

# --- 流转换函数 ---
async def stream_and_convert(payload: ChatPayload):
    client: httpx.AsyncClient = app.state.httpx_client
    coze_payload = {
        "bot_id": settings.coze_bot_id,
        "user": payload.user,
        "query": payload.messages[-1].content,
        "stream": True,
        "chat_history": [m.dict() for m in payload.messages[:-1]]
    }
    headers = {
        "Authorization": f"Bearer {settings.coze_api_token}",
        "Content-Type": "application/json"
    }

    try:
        async with client.stream(
            "POST",
            f"{settings.coze_api_base}/open_api/v2/chat",
            headers=headers,
            json=coze_payload
        ) as response:
            response.raise_for_status()
            buffer = ""
            async for chunk in response.aiter_bytes():
                buffer += chunk.decode('utf-8', errors='ignore')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if not data_str or "[DONE]" in data_str:
                        continue
                    data_json = json.loads(data_str)
                    if data_json.get("event") == "message":
                        msg = data_json.get("message", {})
                        if msg.get("type") == "answer":
                            chunk_text = msg.get("content", "")
                            openai_chunk = {
                                "id": f"chatcmpl-{data_json.get('conversation_id')}",
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": payload.model,
                                "choices": [{"index": 0, "delta": {"content": chunk_text}, "finish_reason": None}]
                            }
                            yield f"data: {json.dumps(openai_chunk)}\n\n"
                    elif data_json.get("event") == "done":
                        break
            yield "data: [DONE]\n\n"
    except httpx.HTTPStatusError as e:
        logger.error("Coze API HTTP error %s: %s", e.response.status_code, e.response.text)
        yield f"data: {json.dumps({'error': e.response.text})}\n\n"
        yield "data: [DONE]\n\n"
    except Exception:
        logger.exception("Unexpected error in stream_and_convert")
        yield f"data: {json.dumps({'error': 'Internal server error'})}\n\n"
        yield "data: [DONE]\n\n"

# --- 路由 ---
@app.post("/v1/chat/completions", response_class=StreamingResponse)
async def chat_completions(
    payload: ChatPayload,
    api_key: APIKey = Depends(get_api_key)
):
    if not payload.stream:
        raise HTTPException(status_code=400, detail="stream must be true")
    logger.info("Request user=%s messages=%d", payload.user, len(payload.messages))
    return StreamingResponse(stream_and_convert(payload), media_type="text/event-stream")

# --- 健康检查 ---
@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        log_level=settings.log_level.lower(),
        workers=int(os.getenv("WORKERS", 1))
    )
