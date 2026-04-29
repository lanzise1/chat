# Project Context

## Purpose

LangChain Chat 是一个最小可跑通、分层清晰的 Chat 应用样板：

- 后端通过 FastAPI + LangGraph 暴露一个 SSE 流式 `/api/chat` 端点
- 通过 MCP（Model Context Protocol）以独立进程形式向 LLM 注入工具能力
- 前端用 Vue 3 + TypeScript 渲染 Markdown / 代码高亮，并支持流式增量与中止生成

目标是让 LLM 应用各层（HTTP 接口、Agent 编排、工具协议、UI）的边界尽量干净，便于二次开发。

## Tech Stack

### Backend (`backend/`)
- Python 3.11+
- FastAPI 0.115 + Uvicorn
- Pydantic v2（接口模型）
- LangChain 0.3 + langchain-openai（LLM 抽象，OpenAI 兼容协议）
- LangGraph 0.2（`create_react_agent` + `InMemorySaver` 做按 `thread_id` 的会话记忆）
- langchain-mcp-adapters（把 MCP 工具映射成 LangChain Tool）
- python-dotenv（`.env` 配置）
- 包管理推荐 `uv`（`uv venv` / `uv pip install -r requirements.txt`）

### MCP Server (`mcp-server/`)
- Python 3.11+
- `mcp` SDK 中的 `FastMCP`，传输层使用 `streamable-http`
- 默认监听 `http://localhost:8765/mcp/`

### Frontend (`frontend/`)
- Vue 3.5 + TypeScript 5.6
- Vite 5（开发态用 `/api` 代理到后端 8000）
- Tailwind CSS 3.4
- markdown-it + highlight.js（Markdown 渲染与代码高亮）
- 包管理：pnpm

## Project Conventions

### Code Style
- Python：`from __future__ import annotations`，全量类型注解，`@dataclass(frozen=True)` 配置对象，模块顶部三引号 docstring 说明职责。
- TypeScript：严格模式，`composables/*` 仅持有状态与逻辑（不渲染），`components/*` 只做 UI、不直接 `fetch`。
- 注释只解释 *为什么*，不重复代码本身在做什么。

### Architecture Patterns

**后端分层（`backend/app/`）**

| 目录 | 职责 |
| --- | --- |
| `api/routes/*` | HTTP 端点：参数解析 + 调 service + 组装响应，不写业务 |
| `services/*` | 业务方法，纯异步函数 / 工厂，不依赖 FastAPI 对象 |
| `schemas/*` | Pydantic 入参 / 出参模型 |
| `core/config.py` | 唯一配置来源（读 env），其它模块只 import `settings` |
| `core/errors.py` | 统一错误判断（如 `is_retryable`） |
| `utils/*` | 无状态纯函数（如 `sse_event`） |

**Agent 编排**：`services/graph.py` 用 `create_react_agent` 构建一次并进程内缓存（`_agent_cache` + `asyncio.Lock` 双检锁）；`services/chat.py` 把 `astream_events(v2)` 翻译成 SSE 事件，工具调用循环交给 LangGraph，本模块只做协议转换。

**会话记忆**：`InMemorySaver` 按 `thread_id` 持久化对话；前端传 `thread_id` 时只发末尾消息，否则走无状态模式（生成一次性 uuid）。生产换 `SqliteSaver` / `PostgresSaver`。

**前端分层（`frontend/src/`）**

| 目录 | 职责 |
| --- | --- |
| `api/http.ts` | fetch 封装，request / response / error 三类拦截器；非 2xx 抛 `ApiError`；**不消费 body**，兼容流式 |
| `api/chat.ts` | 具体接口（`chatStream`、`getHealth`） |
| `utils/sse.ts` | 按 `\n\n` 分包、按 `data:` 抽取 |
| `utils/markdown.ts` | markdown-it + highlight.js 单例 |
| `composables/useChat.ts` | 聊天状态机：消息列表、loading、`AbortController` 中止、清空 |
| `components/ChatView.vue` | 纯 UI |

### Wire Protocol — `POST /api/chat` SSE 事件
```
data: {"type":"delta","content":"片段"}
data: {"type":"tool_call","id":"call_1","name":"get_current_time","args":{...}}
data: {"type":"tool_result","id":"call_1","name":"get_current_time","content":"..."}
data: {"type":"done"}
data: {"type":"error","message":"...","retryable":true}
```
请求体：`{ "messages": ChatMessage[], "thread_id"?: string }`。改协议时前后端必须同步更新。

### Testing Strategy
当前仓库尚未引入测试套件。新增功能优先以「可手测」的方式落地（前端跑 `npm run dev`、后端跑 `uv run python main.py`、MCP 跑 `uv run python server.py`），并在 PR 描述里写清验证步骤。后续若引入测试，建议：

- 后端：`pytest` + `httpx.AsyncClient` 跑 SSE 端到端；MCP 工具用真实子进程或 stub server，避免对 LLM 输出做严格断言。
- 前端：`vitest` + `@vue/test-utils` 覆盖 `composables/useChat`，`utils/sse` 重点覆盖跨包/半包场景。

### Git Workflow
- 主干分支 `main`；提交信息使用中文短句的 conventional 风格前缀（`feat:` / `fix:` / `refactor:` 等），保持历史一致。
- 一次提交一件事，避免「顺手」混入无关重构。

## Domain Context
- **MCP（Model Context Protocol）**：模型与外部工具间的标准化协议。本项目把 MCP 服务端作为独立进程，让工具能力与 Chat 主进程解耦——任何符合 MCP 的服务都能即插即用。
- **SSE 流式**：单向、长连接、文本协议；前端用 `fetch` + `ReadableStream` 解析，比 WebSocket 更轻；中止靠 `AbortController`。
- **OpenAI 兼容 API**：`OPENAI_BASE_URL` 可指向 DeepSeek / Ollama 等，无需改代码。

## Important Constraints
- **无数据库**：会话记忆只在进程内（`InMemorySaver`），重启即失。线上化前必须替换 checkpointer。
- **CORS**：开发态前端走 Vite 代理；生产同域部署，`CORS_ORIGINS` 默认仅放行 `http://localhost:5173`。
- **MCP 可选**：`MCP_ENABLED=false` 时不连工具，纯 LLM 对话仍可用，便于离线 / 鉴权失败时降级。
- **Windows 友好**：开发主机为 Windows，shell 脚本需兼容 Git Bash；路径用正斜杠。

## External Dependencies
- **OpenAI 兼容 LLM**：`OPENAI_API_KEY` + 可选 `OPENAI_BASE_URL`、`OPENAI_MODEL`（默认 `gpt-4o-mini`）。
- **MCP 服务端**：默认 `http://localhost:8765/mcp/`，由 `mcp-server/server.py` 提供 `get_current_time` / `add` / `echo` / `get_weather` 等示例工具。
- 无外部数据库 / 队列 / 缓存依赖。
