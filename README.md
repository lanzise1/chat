# LangChain Chat

一个分层清晰、最小可跑通的 Chat 应用:

- **后端**:Python + FastAPI + LangChain,SSE 流式输出,无数据库
- **MCP 服务端**:独立 Python 进程,通过 streamable-http 暴露 demo 工具
- **前端**:Vue 3 + TypeScript + Tailwind CSS + markdown-it,支持 Markdown + 代码高亮 + 流式渲染 + 中止生成

## 目录结构

```
chat/
├── backend/
│   ├── main.py                       # ASGI 入口 + uvicorn 启动
│   └── app/
│       ├── __init__.py               # create_app() 应用工厂
│       ├── core/config.py            # Settings(读取 .env)
│       ├── schemas/chat.py           # Pydantic 模型(接口层数据结构)
│       ├── services/
│       │   ├── llm.py                # LangChain LLM 构造 / 消息转换
│       │   ├── retry.py              # 首个 chunk 到达前的重试
│       │   ├── mcp_client.py         # MCP 客户端(加载远端 tools)
│       │   └── chat.py               # 流式生成 + 工具调用循环
│       ├── api/
│       │   ├── router.py             # 聚合 API 路由
│       │   └── routes/               # 接口按文件划分
│       │       ├── health.py
│       │       └── chat.py
│       └── utils/sse.py              # SSE 事件格式化
│
├── mcp-server/                       # 独立 MCP 服务端
│   ├── server.py                     # FastMCP + streamable-http
│   ├── requirements.txt
│   └── README.md
│
└── frontend/
    └── src/
        ├── main.ts
        ├── App.vue
        ├── style.css
        ├── types/chat.ts             # 共享类型定义
        ├── api/
        │   ├── http.ts               # fetch 封装 + 请求/响应/错误三类拦截器 + ApiError
        │   └── chat.ts               # 具体接口调用(chatStream / getHealth)
        ├── utils/
        │   ├── sse.ts                # SSE 流解析
        │   ├── markdown.ts           # markdown-it + highlight.js
        │   └── dom.ts                # 滚动 / textarea 自适应
        ├── composables/useChat.ts    # 聊天状态 + 流式逻辑(无 UI)
        └── components/ChatView.vue   # 纯 UI
```

## 快速开始

### 1) 启动 MCP 服务端

```bash
cd mcp-server
uv venv # 创建虚拟环境
uv pip install -r requirements.txt # 安装依赖
uv run python server.py   # 默认 http://localhost:8765/mcp/

```

内置工具:`get_current_time` / `add` / `echo` / `get_weather`(假数据)。

### 2) 启动后端(推荐 uv)

```bash
cd backend
uv venv
uv pip install -r requirements.txt
cp .env.example .env   # 编辑 .env,填入 OPENAI_API_KEY
uv run python main.py  # 默认 http://localhost:8000
```

不用 uv:

```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```

`.env` 示例:

```ini
OPENAI_API_KEY=sk-xxxxxx
OPENAI_MODEL=gpt-4o-mini
# 可换成任意 OpenAI 兼容服务:
# OPENAI_BASE_URL=https://api.deepseek.com/v1
# OPENAI_BASE_URL=http://localhost:11434/v1   # 本地 Ollama

# MCP:指向步骤 1 启动的服务端
MCP_ENABLED=true
MCP_SERVER_URL=http://localhost:8765/mcp/
```

### 3) 启动前端

```bash
cd frontend
npm install
npm run dev   # 默认 http://localhost:5173
```

Vite 已配置代理,前端 `/api/*` 会被转发到 `http://localhost:8000`,生产部署时同域即可、无需额外 CORS 处理。

## 架构要点

**调用链**:前端 → 后端 `/api/chat` → LangChain LLM(`bind_tools`) →(如模型发起 tool_calls)→ 后端 MCP 客户端 → MCP 服务端工具 → 结果回灌 LLM → SSE 推回前端。

**后端分层**

| 目录           | 职责                                           |
| -------------- | ---------------------------------------------- |
| `api/routes/*` | HTTP 端点,仅做参数解析 + 调 service + 组装响应 |
| `services/*`   | 业务方法,不依赖 FastAPI                        |
| `schemas/*`    | 入参 / 出参模型                                |
| `core/config`  | 统一配置来源                                   |
| `utils/*`      | 无状态纯函数                                   |

**前端分层**

| 目录                      | 职责                                                                                                   |
| ------------------------- | ------------------------------------------------------------------------------------------------------ |
| `api/http.ts`             | fetch 封装,挂三类拦截器(request / response / error),非 2xx 统一抛 `ApiError`,**不消费 body**(兼容流式) |
| `api/chat.ts`             | 具体接口调用,返回 Promise / 驱动回调                                                                   |
| `utils/sse.ts`            | 按 `\n\n` 解析 SSE、按 `data:` 抽取数据                                                                |
| `utils/markdown.ts`       | markdown-it + highlight.js 单例                                                                        |
| `composables/useChat.ts`  | 聊天状态机(消息列表、loading、中止、清空)                                                              |
| `components/ChatView.vue` | 纯 UI,无直接 `fetch`                                                                                   |

## 接口

`POST /api/chat`

```json
{
  "messages": [
    { "role": "user", "content": "你好" },
    { "role": "assistant", "content": "你好!" },
    { "role": "user", "content": "介绍下你自己" }
  ]
}
```

响应(SSE):

```
data: {"type":"delta","content":"片段"}
data: {"type":"tool_call","id":"call_1","name":"get_current_time","args":{"timezone":"Asia/Shanghai"}}
data: {"type":"tool_result","id":"call_1","name":"get_current_time","content":"2026-04-23 22:30:00 CST"}
data: {"type":"delta","content":"现在是 ..."}
data: {"type":"done"}
```

错误:

```
data: {"type":"error","message":"..."}
```
