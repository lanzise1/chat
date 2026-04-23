## Backend (LangChain + FastAPI)

分层结构:

```
backend/
├── main.py                        # ASGI 入口 + uvicorn 启动
└── app/
    ├── __init__.py                # create_app() 应用工厂
    ├── core/config.py             # Settings(读取 .env)
    ├── schemas/chat.py            # Pydantic 模型
    ├── services/
    │   ├── llm.py                 # LangChain LLM 构造 / 消息转换
    │   └── chat.py                # 流式生成器
    ├── api/
    │   ├── router.py              # 聚合 API 路由
    │   └── routes/
    │       ├── health.py          # GET  /api/health
    │       └── chat.py            # POST /api/chat
    └── utils/sse.py               # SSE 事件格式化
```

### 安装 & 运行(uv)

```bash
cd backend
uv venv
uv pip install -r requirements.txt
cp .env.example .env                 # 填 OPENAI_API_KEY
uv run python main.py                # 默认 http://localhost:8000
# 或:
uv run uvicorn main:app --reload --port 8000
```

不用 uv 也行:

```bash
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
python main.py
```

### 接口

- `GET  /api/health` — 健康检查
- `POST /api/chat` — 流式聊天,`text/event-stream`

请求体:

```json
{
  "messages": [
    { "role": "user", "content": "你好" },
    { "role": "assistant", "content": "你好!" },
    { "role": "user", "content": "介绍下你自己" }
  ]
}
```

SSE 事件:

```
data: {"type":"delta","content":"片段文本"}
data: {"type":"done"}
data: {"type":"error","message":"..."}
```

### 新增路由步骤

1. 在 `app/api/routes/` 下新建 `foo.py`,定义 `router = APIRouter()` 与具体端点
2. 在 `app/api/router.py` 里 `api_router.include_router(foo.router, tags=["foo"])`
3. 业务方法放 `app/services/`,数据模型放 `app/schemas/`
