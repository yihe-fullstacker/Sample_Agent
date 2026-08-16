# Wedding Multi-Agent 婚礼策划多智能体系统

基于 LangChain / LangGraph 的 Subagents 模式实现。

## 项目结构

```
wedding_app/
├── agents/          # 各专业 Agent
│   ├── travel_agent.py
│   ├── venue_agent.py
│   ├── playlist_agent.py
│   └── coordinator.py
├── api/             # API 层（预留）
├── common/          # 公共工具、状态定义
│   ├── state.py
│   └── tools.py
├── db/              # 数据库相关
├── models/          # 数据模型
├── static/          # 静态资源
├── main.py          # 入口
├── __init__.py
├── .gitignore
└── README.md
```

## 快速开始

1. 安装依赖：`pip install -r ../requirements.txt`
2. 配置环境变量：复制 `../.env.example` 为 `.env` 并填入密钥
3. 运行：`python -m wedding_app.main` 或 `python main.py`

## 核心功能

- **Travel Agent**：查询往返机票（MCP Kiwi + Time）
- **Venue Agent**：搜索婚礼场地（Tavily）
- **Playlist Agent**：根据风格筛选歌单并计算预算（SQLite）
- **Coordinator**：主协调者，收集信息并委派任务
