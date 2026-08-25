"""
星尘 · 个人智能助手
入口文件 - 按照 KnowledgeBase_RAG 架构组织

启动方式:
  python main.py
  或
  uvicorn main:app --reload --host 0.0.0.0 --port 8010
"""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.routes import router
from common.config import get_settings
from common.logger import setup_logger

# 加载 .env
load_dotenv()

settings = get_settings()
logger = setup_logger("main")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于 LangGraph 的个人智能助手，支持日程、Todo、邮件智能安排与冲突检测",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由
app.include_router(router, prefix="/api")

# 静态文件
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index():
    """前端首页"""
    return FileResponse(STATIC_DIR / "index.html")


@app.on_event("startup")
async def startup():
    logger.info(f"{settings.app_name} v{settings.app_version} starting...")
    logger.info(f"LLM: {settings.llm_model} @ {settings.openai_api_base}")
    # 预热 Graph
    from agents.assistant import get_assistant_graph
    get_assistant_graph()
    logger.info(f"Graph ready. Open http://localhost:{settings.port}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
