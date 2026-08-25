# 星尘 · 个人智能助手 (PersonalAssistant)

基于 **LangGraph** 构建的个人智能助手，完整实现 PDF 文档中的核心概念：

- Node / Edge / State
- ReAct 工具调用循环
- MessagesState + Checkpointer 会话记忆
- 条件边路由
- 流式输出

## 项目结构（对齐 KnowledgeBase_RAG 架构）

```
PersonalAssistant/
├── agents/           # LangGraph Agent 与工具
│   ├── assistant.py  # Graph 构建（ReAct）
│   └── tools.py      # 日程/Todo/邮件/智能安排工具
├── api/              # FastAPI 路由
│   └── routes.py     # /api/chat 与 /api/chat/stream
├── common/           # 公共配置与日志
│   ├── config.py
│   └── logger.py
├── db/               # 模拟数据（可替换为真实 DB/API）
│   └── mock_data.py
├── models/           # Pydantic Schema
│   └── schemas.py
├── resources/        # 系统提示词等资源
│   └── system_prompt.txt
├── static/           # 前端
│   ├── css/style.css
│   ├── js/app.js
│   └── index.html
├── main.py           # 入口
├── requirements.txt
└── README.md
```

## 核心功能

1. **查看明天日程** — `get_tomorrow_schedule`
2. **查询 Todo / 邮件** — `get_todos` / `get_emails`
3. **智能安排明天工作** — `arrange_tomorrow_work`
   - 综合日程 + 高优 Todo + 紧急邮件
   - 自动检测时间冲突
   - 给出具体调整建议（时间段 + 任务）

## 快速启动

```bash
# 1. 安装依赖
cd PersonalAssistant
pip install -r requirements.txt

# 2. 配置环境变量（可选，默认 DeepSeek）
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY / OPENAI_API_BASE / LLM_MODEL

# 3. 启动
python main.py
```

浏览器打开 http://localhost:8010

> 注：KnowledgeBase_RAG 占用 8000 端口，本项目固定使用 **8010**，两者可同时运行、互不冲突。

> 本机如使用 `D:\Langchain\jupyter\.venv`，可直接：
> `D:\Langchain\jupyter\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8010`

## 环境变量

| 变量 | 说明 | 默认 |
|------|------|------|
| OPENAI_API_KEY | API Key | - |
| OPENAI_API_BASE | API Base URL | https://api.deepseek.com |
| LLM_MODEL | 模型名 | deepseek-chat |

## 架构说明

完全遵循 PDF 文档《第1节 基本概念》《第2节 常见WorkFlow》《第3节 Think In LangGraph》中的设计思想：

- **State**: `MessagesState`（带 `add_messages` Reducer）
- **Node**: `agent`（LLM）+ `tools`（ToolNode）
- **Edge**: 条件边 `should_continue` 实现 ReAct 循环
- **Memory**: `InMemorySaver` + `thread_id`
- **Streaming**: `astream_events` (v2)

## 前端界面（商业级视觉）

前端为纯静态实现（无外部 CDN 依赖），采用「深邃星夜 · 玻璃态」设计语言：

- **视觉体系**：紫罗兰渐变品牌色 + 极光青点缀，星点夜空背景、玻璃拟态面板、渐变光晕
- **欢迎屏**：品牌头像 + 功能卡片（明天日程 / 智能安排 / 冲突检测 / 未读邮件），一键发起对话
- **流式体验**：SSE 逐 token 渲染、工具调用徽章（加载/完成态）、闪烁光标、打字指示器
- **对话能力**：Markdown 完整渲染（标题、列表、表格、代码块、引用）、消息时间、一键复制、会话计数
- **会话管理**：新对话 / 清空对话（记忆基于 `thread_id`）
- **工程化细节**：后端健康检查（侧边栏实时状态）、Enter 发送 / Shift+Enter 换行、自动增高输入框、停止生成（AbortController）
- **响应式**：桌面侧边栏 + 移动端抽屉导航，适配 390px 手机视口
- **无障碍**：focus-visible 焦点环、ARIA 标签、`prefers-reduced-motion` 减少动效

## 联调自检

```bash
# 健康检查
curl http://localhost:8010/api/health

# 普通对话
curl -X POST http://localhost:8010/api/chat -H "Content-Type: application/json" \
  -d '{"message":"帮我看看明天的日程"}'

# SSE 流式对话（推荐前端使用）
curl -N -X POST http://localhost:8010/api/chat/stream -H "Content-Type: application/json" \
  -d '{"message":"帮我安排明天的工作"}'
```
