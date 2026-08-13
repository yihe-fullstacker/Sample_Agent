import os
import sys

# 保证无论从项目根目录直接运行 python main.py，还是以 python -m Email_app.main
# 方式运行，都能把上级目录（项目根）加入 sys.path，从而正确导入 Email_app 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn  #运行 FastAPI 应用的 ASGI 服务器
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from Email_app.api.v1 import chat
from Email_app.api.v1 import sessions
from Email_app.common.logger import setup_logging
from contextlib import asynccontextmanager
from Email_app.agents.email_agent import email_agent
from dotenv import load_dotenv

#EmailAgent 项目的“总入口 / 启动中心

#                         main.py
#                            │
#             ┌──────────────┼──────────────┐
#             ↓              ↓              ↓
#          chat.py       sessions.py    email_agent.py
#             │              │              │
#             ↓              ↓              ↓
#          对话 API        会话 API       Agent
#                            │              │
#                            ↓              ↓
#                       SQLite DB       LangGraph
#                                           │
#                                           ↓
#                                      Checkpointer

# 初始化日志配置
setup_logging()

# 加载环境变量
load_dotenv()


# 使用 lifespan 管理 checkpointer 生命周期 (对应 PDF 第 57 页)
#   FastAPI 应用启动和关闭时，需要执行什么操作
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化 checkpointer 和 agent
    await email_agent.init()
    yield #启动前后的中止条件
    # 停机时，关闭连接
    await email_agent.close()

#创建 FastAPI 应用
app = FastAPI(
    title="Personal Chief API",
    description="私厨",
    version="0.1.0",
    lifespan=lifespan
)

#app. 都是在给这个app添加功能
#例如：
#app.add_middleware()
#app.include_router()
#app.mount()
#@app.get()

# 1. 配置跨域资源共享 (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议指定插件的 ID 或具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 挂载路由
app.include_router(chat.router, prefix="/api/v1", tags=["对话"])
app.include_router(sessions.router, prefix="/api/v1", tags=["会话管理"])

# 3. 挂载前端资源
# 让 FastAPI 同时负责提供前端静态文件
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


# 前端 fallback 路由 - 只处理非 API 请求
# 解决：SPA 单页应用刷新页面时 404 的问题
#意思是： 如果服务器找不到对应的真实文件，就把 index.html 返回给 Vue，让 Vue 自己处理 /chat
@app.get("/{path:path}", include_in_schema=False)
async def serve_frontend(path: str):
    # 排除 API 路径
    if path.startswith("api/"):
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "Not Found"}, status_code=404)

    # 如果请求的是静态文件，直接返回
    file_path = os.path.join(static_dir, path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)

    # 否则返回 index.html（SPA fallback）
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    return {"message": "你的独家私厨上线了~", "status": "ok"}


if __name__ == "__main__":
    # 启动命令：python -m Email_app.main 或者是直接 python main.py
    uvicorn.run("Email_app.main:app", host="127.0.0.1", port=8001, reload=True)

# 总结：
#main.py
#   │
#   ├── 加载配置
#   ├── 初始化日志
#   ├── 初始化数据库
#   ├── 初始化各种服务
#   ├── 注册路由
#   ├── 注册中间件
#   ├── 注册插件
#   ├── 管理应用生命周期
#   └── 启动服务器
#
#Agent 通常不是被 main.py 直接调用，而是被“业务层”调用；
# 在你这个 FastAPI EmailAgent 项目里，主要就是 Router（如 chat.py、sessions.py）调用 email_agent
