# 知了 · 个人知识库 RAG Agent

基于本课程《构建知识库 → RAG Agent → RAG 评估》全部知识点实现的 **Agentic RAG** 个人知识库系统。

## 架构（对齐参考目录结构）

```
KnowledgeBase_RAG/
├── agents/          # Agentic RAG（create_agent + @tool 检索）
├── api/             # FastAPI 路由
├── common/          # 配置
├── db/              # 向量库（Chroma + DashScope Embedding）
├── models/          # Pydantic Schema
├── static/          # 前端（聊天 UI）
├── resources/       # 默认知识（评估.md）
├── uploads/         # 用户上传
├── db_data/         # Chroma 持久化
├── main.py
└── requirements.txt
```

## 核心能力（对应课程知识点）

| 能力 | 实现 |
|------|------|
| 文档加载 | Markdown / 纯文本，MarkdownHeaderTextSplitter + RecursiveCharacterTextSplitter |
| Embedding | DashScope `text-embedding-v3` |
| 向量库 | Chroma 持久化 |
| Agentic RAG | `create_agent` + `search_knowledge_base` Tool，LLM 自主决定是否检索 |
| 前端 | 侧边栏上传 + 对话区，展示检索来源 |
| 默认知识 | 启动时自动加载 `resources/评估.md`（教育学考点） |

## 快速开始

### 1. 环境变量

复制并填写：

```bash
# .env
DASHSCOPE_API_KEY=sk-xxx          # 阿里云百炼 Embedding
DEEPSEEK_API_KEY=sk-xxx           # DeepSeek Chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 2. 安装依赖

```bash
cd KnowledgeBase_RAG
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 启动

```bash
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

浏览器打开：**http://127.0.0.1:8000**

### 4. 使用

1. 左侧可上传 `.md` / `.txt`，或粘贴文本索引
2. 右侧对话；勾选「启用知识库检索」走 Agentic RAG
3. 可问：`孔子的教育思想有哪些？`、`孟子和荀子人性论有何不同？`

## API 摘要

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/stats` | 知识库统计 |
| GET | `/api/documents` | 文档列表 |
| POST | `/api/upload` | 上传文件 |
| POST | `/api/upload_text` | 粘贴文本 |
| POST | `/api/chat` | 对话 `{message, session_id, use_rag}` |
| DELETE | `/api/knowledge` | 清空知识库 |

## 与课程对应关系

- **第1节 构建知识库**：`db/vector_store.py`（Loader 思路、切分、Embedding、Chroma）
- **第2节 RAG Agent**：`agents/rag_agent.py`（Agentic RAG + Tool）
- **第3节 RAG 评估**：可在此基础上用 RAGAS 对 `/api/chat` 结果做离线评估（数据集字段：user_input / retrieved_contexts / response / reference）
- **第4章 Agentic RAG**：外挂知识库解决幻觉与时效问题

## 扩展建议

- 接入 BM25 + RRF + Cross-Encoder 做混合检索（参考第2节综合优化）
- 增加 PDF 上传（PyPDF / MinerU）
- 用 RAGAS 写离线评估脚本
- 多用户 session 持久化到 Redis / SQLite
