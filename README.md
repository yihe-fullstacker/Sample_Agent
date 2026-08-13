# MailFriend 智能邮箱助手（Email App）

基于 **FastAPI + LangChain/LangGraph** 构建的智能邮箱助手，后端提供 SSE 流式对话接口，前端为纯静态页面（`static/`）。Agent 只有在用户完成邮箱鉴权后，才会开放“查看收件箱 / 发送邮件”等工具；发送邮件前还会经过 **HITL（Human-in-the-Loop）人工确认**，由用户批准、拒绝或修改邮件内容。

> 演示环境说明：收件箱和邮件发送均为**模拟数据/模拟操作**，不会真实收发邮件。

---

## 功能特性

- **邮箱账号鉴权**：未鉴权时 Agent 只能使用 `authenticate` 工具，鉴权通过后才可使用 `check_inbox` / `send_email`
- **动态工具与动态提示词**：根据当前会话的 `authenticated` 状态，自动切换本轮可用的工具和 System Prompt
- **SSE 流式响应**：Agent 的生成过程（LLM token、中断事件）通过 Server-Sent Events 实时推送到前端
- **HITL 人工确认**：发送邮件前弹出确认框，支持 批准 / 拒绝（附原因）/ 编辑后发送
- **会话管理**：创建会话、会话列表、历史消息、删除会话；LangGraph Checkpointer 保存每个会话的完整状态
- **简单前端**：无需构建，纯 HTML/CSS/JS，开箱即用

---

## 技术栈

| 组件 | 说明 |
| --- | --- |
| FastAPI + Uvicorn | Web 框架与 ASGI 服务器 |
| LangChain 1.x | `create_agent`、工具、中间件 |
| LangGraph | Checkpointer、状态管理与中断恢复 |
| DeepSeek | 默认 LLM（`deepseek-chat`） |
| SQLite + aiosqlite | 会话状态（Checkpointer）与会话列表持久化 |
| sse-starlette | SSE 流式响应 |
| 前端 | 原生 HTML / CSS / JavaScript + marked.js |

---

## 项目结构

```
Email_app/
├── main.py                 # FastAPI 入口：路由、静态资源、lifespan 初始化 Agent
├── __init__.py             # Email_app 包标记
├── agents/
│   └── email_agent.py      # EmailAgent：工具定义、中间件、SSE 生成、历史消息
├── api/
│   └── v1/
│       ├── chat.py         # 聊天相关接口（/chat/send、/chat/stream、/chat/messages）
│       └── sessions.py     # 会话管理接口（/sessions）
├── common/
│   └── logger.py           # 日志配置
├── models/
│   ├── schemas.py          # 请求模型（ChatRequest）
│   └── session.py          # 会话 Pydantic 模型 + 会话表 CRUD
├── db/                     # 数据目录（运行时生成数据库）
│   ├── mail_fiend.db       # LangGraph Checkpointer 数据库（自动创建）
│   ├── sessions.db         # 会话列表数据库（自动创建）
│   └── personal_chief.db   # 历史遗留数据库（未使用）
└── static/                 # 前端静态资源
    ├── index.html          # 前端页面（与 email.html 内容一致，便于根路径访问）
    ├── email.html
    ├── app.js
    ├── style.css
    └── marked.min.js
```

---

## 环境准备

### 1. Python 与依赖

项目依赖 Python 3.13，已在上级目录虚拟环境中安装（`D:\Langchain\jupyter\.venv`），主要依赖见上级目录的 `pyproject.toml`：

- `fastapi`、`uvicorn`
- `langchain>=1.2.3`、`langchain-deepseek`
- `langgraph`、`langgraph-checkpoint-sqlite`
- `sse-starlette`
- `aiosqlite`、`python-dotenv`

如果要在新环境安装，可在上级目录执行：

```powershell
uv sync
```

### 2. 环境变量（.env）

程序启动时会通过 `load_dotenv()` 自动向上查找 `.env` 文件。当前项目直接复用上级目录 `D:\Langchain\jupyter\.env`，无需额外配置。

| 变量 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `DEEPSEEK_API_KEY` | 是 | - | DeepSeek 模型 API Key |
| `MODEL_NAME` | 否 | `deepseek-chat` | Agent 使用的模型名 |
| `LANGSMITH_API_KEY` / `LANGSMITH_TRACING` | 否 | - | LangSmith 链路追踪 |

> 若把项目移动到其他目录，请在该目录（或上级任意目录）放置包含 `DEEPSEEK_API_KEY` 的 `.env` 文件。

---

## 启动运行

### 方式一：在 Email_app 目录内直接运行（推荐）

```powershell
cd D:\Langchain\jupyter\Email_app
..\.venv\Scripts\python.exe main.py
```

### 方式二：在父目录以包方式运行

```powershell
cd D:\Langchain\jupyter
.venv\Scripts\python.exe -m Email_app.main
```

启动成功后浏览器访问：

```
http://127.0.0.1:8001/
```

默认端口为 `8001`，如需修改可编辑 `main.py` 末尾的 `port` 参数。

---

## 使用说明

1. 打开首页后，点击 **“新建会话”** 创建会话（默认 `user_id=default`，业务类型 `email-assistant`）
2. 在输入框向 Agent 提问，例如“帮我看一下收件箱”
3. Agent 会要求先完成邮箱鉴权，请提供演示账号：

   - 邮箱：`huge@itcast.cn`
   - 密码：`123`

4. 鉴权通过后，Agent 可查看收件箱；当它准备**发送邮件**时，前端会弹出确认框：
   - **Approve**：批准发送
   - **Reject**：拒绝并填写原因
   - **Edit**：修改收件人/主题/内容后确认

---

## API 文档

所有接口前缀为 `/api/v1`。启动后也可直接查看 Swagger 文档：`http://127.0.0.1:8001/docs`

### 聊天接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/v1/chat/send` | 发送消息，SSE 流式返回 Agent 响应（含 HITL 中断） |
| POST | `/api/v1/chat/stream` | 同上（历史兼容接口） |
| GET | `/api/v1/chat/messages?thread_id={id}` | 获取指定会话历史消息 |
| DELETE | `/api/v1/chat/messages?thread_id={id}` | 清空指定会话历史 |

请求示例（PowerShell）：

```powershell
$body = '{"message":"帮我看一下收件箱","thread_id":"<thread_id>"}'
Invoke-WebRequest -Method Post -Uri 'http://127.0.0.1:8001/api/v1/chat/send' `
  -ContentType 'application/json' -Body $body
```

SSE 事件格式：

```json
// LLM 流式输出
event: message
data: {"type": "message", "content": "需要先确认您的身份"}

// HITL 中断，等待人工确认
event: interrupt
data: {"type": "interrupt", "interrupt": {"reason": "需要人工确认", "details": [...]}}

// 处理完成
event: done
data: {"type": "done", "content": "处理完成"}
```

### 会话管理接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/v1/sessions` | 创建会话 |
| GET | `/api/v1/sessions?user_id=&biz_type=` | 查询会话列表 |
| DELETE | `/api/v1/sessions/{thread_id}` | 删除会话（同时清理 Checkpointer 状态） |
| GET | `/api/v1/sessions/{thread_id}/messages` | 获取会话历史消息 |

创建会话请求体：

```json
{
  "user_id": "default",
  "biz_type": "email-assistant",
  "name": "新会话"
}
```

---

## 核心设计说明

### Agent 工作流（鉴权状态机）

会话状态 `AuthenticatedState` 中维护 `authenticated` 字段：

1. **未鉴权**：动态中间件只暴露 `authenticate` 工具，System Prompt 提示必须先验证身份
2. **鉴权中**：用户提供邮箱密码，`authenticate` 工具校验（演示账号 `huge@itcast.cn` / `123`）并通过 `Command` 更新状态
3. **已鉴权**：开放 `check_inbox` / `send_email` 工具，可正常查收件箱、发邮件

### 中间件

- `dynamic_tool_call`（`wrap_model_call`）：根据 `authenticated` 动态决定本轮 LLM 可用的工具
- `dynamic_prompt_func`（`dynamic_prompt`）：根据鉴权状态切换 System Prompt
- `HumanInTheLoopMiddleware`：`send_email` 执行前触发人工确认，`authenticate` / `check_inbox` 自动执行

### 会话持久化

- LangGraph `AsyncSqliteSaver` 写入 `db/mail_fiend.db`，按 `thread_id` 保存每个会话的 Checkpoint
- 会话列表（名称、时间等）由 `models/session.py` 写入 `db/sessions.db`
- 通过 `thread_id` 可恢复任意会话的完整状态并继续对话

---

## 常见问题

### 1. IDE 报“未解析的引用”

项目内部导入统一使用 `Email_app.*` 全限定包路径（例如 `from Email_app.agents.email_agent import email_agent`）。如果 IDE 无法解析，请确认：

- PyCharm 项目根目录为 `D:\Langchain\jupyter`（或已将 `Email_app` 的上级目录加入 Source Root）
- 用 `python main.py` 或 `python -m Email_app.main` 运行，二者都已支持

### 2. 启动报 `ModuleNotFoundError: No module named 'Email_app'`

请确认当前工作目录：

- 直接运行：`cd D:\Langchain\jupyter\Email_app` 后执行 `..\.venv\Scripts\python.exe main.py`
- 包方式运行：`cd D:\Langchain\jupyter` 后执行 `.venv\Scripts\python.exe -m Email_app.main`

### 3. 端口被占用

修改 `main.py` 中 `uvicorn.run(..., port=8001)` 的端口号，或先释放 8001 端口。

### 4. 调用模型报鉴权失败

确认 `DEEPSEEK_API_KEY` 已配置在 `.env` 中，且 `.env` 位于当前目录或其上级目录。

### 5. 收件箱/邮件是真实的吗？

不是。`check_inbox` 返回两封内置的模拟邮件，`send_email` 仅返回一条发送成功的提示文本，用于演示 Agent 完整流程，不会连接真实邮箱服务。

---

## 演示账号

| 项目 | 值 |
| --- | --- |
| 邮箱 | `huge@itcast.cn` |
| 密码 | `123` |
