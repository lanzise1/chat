# Repository Guidelines for AI Agents

本文件是面向所有自动化代码助手（Claude Code、Cursor、Copilot 等）的入口说明。配合 `openspec/project.md` 一起阅读：`project.md` 描述系统是什么、长什么样；本文件描述在这个仓库里**如何动手做事**。

## 项目速览

LangChain Chat 由三个相互独立的进程组成：

| 模块         | 路径          | 启动命令                  | 默认端口 |
| ------------ | ------------- | ------------------------- | -------- |
| 后端 API     | `backend/`    | `uv run python main.py`   | 8000     |
| MCP 工具服务 | `mcp-server/` | `uv run python server.py` | 8765     |
| 前端         | `frontend/`   | `pnpm dev`                | 5173     |

调用链：`frontend → POST /api/chat (SSE) → LangGraph ReAct agent → MCP tools → LLM → SSE 推回前端`。

## 工作前置约定

1. **先读 `openspec/project.md`**，确认技术栈、分层与约束。
2. **改协议要双向同步**：`POST /api/chat` 的请求体与 SSE 事件类型（`delta` / `tool_call` / `tool_result` / `done` / `error`）是前后端契约，任意一侧变动需同步另一侧。
3. **不要把业务写进 `api/routes/*`**：路由只做参数解析 + 调用 service + 组装响应。业务进 `services/`，模型进 `schemas/`，配置进 `core/config.py`。
4. **前端 UI 不直接 `fetch`**：网络调用走 `api/*`，状态/逻辑走 `composables/*`，组件只渲染。
5. **配置只从 `settings` 取**：禁止在业务代码里散落 `os.getenv`。新增配置加到 `backend/app/core/config.py` 的 `Settings` 数据类，并在 README / `.env.example` 同步示例。

## 编码规范

### Python（后端 / MCP）

- 模块顶部加三引号 docstring，说明该文件的职责（参考 `services/chat.py`、`services/graph.py`）。
- 文件首行用 `from __future__ import annotations`；类型注解齐全；不要用 `Any` 兜底，除非确实是动态结构。
- 配置类用 `@dataclass(frozen=True)`，全局以 `settings = Settings()` 暴露。
- 异步函数用 `async def`；进程内单例（如 agent / mcp client）用 `asyncio.Lock` + 双检锁，参考 `services/graph.py`。
- 异常：业务可恢复错误走 `core/errors.is_retryable`，对外的 SSE 错误事件统一格式 `{type: "error", message, retryable}`。
- 注释只写 _为什么_；显然的代码不要复述。

### TypeScript / Vue（前端）

- 严格模式 TypeScript；公用类型放 `src/types/`。
- 网络层放 `src/api/`，使用 `api/http.ts` 的封装并统一抛 `ApiError`；**不要在拦截器里 `await response.text()`**——会把流式响应吃掉。
- 状态用 `composables/useChat`；组件 `<script setup lang="ts">`，UI 与状态分离。
- Markdown 渲染调用 `utils/markdown.ts` 的单例，避免每帧重建。
- 流解析永远用 `utils/sse.ts`，不要在组件里手写 `\n\n` 分包。

## 协议守则

`ChatRequest`：

```ts
{ messages: ChatMessage[]; thread_id?: string }
```

- 带 `thread_id` ⇒ 启用 LangGraph `InMemorySaver` 记忆，**只发末尾新消息**。
- 不带 `thread_id` ⇒ 无状态，**重发完整消息历史**；后端会临时 mint 一个一次性 uuid。

SSE 事件类型必须是以下之一，新增类型需同时改：

- `backend/app/services/chat.py`（生产端）
- `frontend/src/utils/sse.ts` + `composables/useChat.ts`（消费端）
- `README.md` 与 `openspec/project.md` 的协议章节

## 启动与本地验证

最小本地链路（按顺序起三个进程）：

```bash
# MCP（可选；MCP_ENABLED=false 时可跳过）
cd mcp-server && uv run python server.py

# 后端
cd backend && cp .env.example .env  # 填 OPENAI_API_KEY
uv run python main.py

# 前端
cd frontend && pnpm install && pnpm dev
```

UI / 流式相关的改动**必须**在浏览器里手测后再报告完成；只跑类型检查不算验证。golden path：发一条会触发工具调用的话（如「现在几点」），观察 `tool_call` / `tool_result` / `delta` 顺序和最终 Markdown 渲染。

## OpenSpec 工作流

本仓库使用 OpenSpec 管理需求变更：

- 提议新功能 / 改动：用 `openspec-propose`（或 `opsx:propose`），生成 proposal + design + tasks + spec delta。
- 探索性讨论：用 `openspec-explore`。
- 开始实现：用 `openspec-apply-change`。
- 完成归档：用 `openspec-archive-change`。

变更产物落在 `openspec/changes/<change-id>/`，已归档的进 `openspec/changes/archive/`，最终规范进 `openspec/specs/`。**对协议、分层或外部依赖的改动建议先走 OpenSpec proposal，再写代码。**

## 提交与 PR

- 提交信息用中文 + conventional 前缀：`feat:` / `fix:` / `refactor:` / `docs:` / `chore:`，保持与 `git log` 历史风格一致。
- 一个提交一件事，禁止顺手夹带无关重构。
- 修改协议或新增配置项的 PR，描述里必须列出：
  - 改了哪些事件 / 字段
  - 前后端 / `.env.example` / 文档是否已同步
  - 本地手测步骤与结果
- 不要主动 `git push` / 建 PR，除非用户明确要求。

## 不要做的事

- 不要引入新的全局可变状态（agent / mcp client 之外）。
- 不要在 `api/routes/*` 里 `await llm` 或处理工具调用——那是 `services/` 的事。
- 不要把 `InMemorySaver` 当作「会话存储」来设计长期功能；它进程内重启即丢。
- 不要为流式响应加「先 `await response.text()` 再判断」的拦截器——会把流吃掉。
- 不要在没有用户明确同意的情况下改 `requirements.txt` / `package.json` 主版本，或换包管理器。
- 不要新建散落的 Markdown 笔记 / 设计文档；所有跨会话信息进 `openspec/` 或现有 README。
