"""个人知识库 RAG Agent 入口。"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import router
from common.config import STATIC_DIR, RESOURCES_DIR
from db.vector_store import kb

app = FastAPI(
    title="个人知识库 RAG Agent",
    description="基于 LangChain Agentic RAG 的个人知识库问答系统",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# 静态资源
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
async def startup():
    """启动时尝试加载 resources 下的默认知识。"""
    default_md = RESOURCES_DIR / "评估.md"
    if default_md.exists() and not kb.list_documents():
        try:
            doc_id, n = kb.add_file(default_md, filename="评估.md")
            print(f"[startup] 已加载默认知识库: {doc_id} ({n} chunks)")
        except Exception as e:
            print(f"[startup] 加载默认知识失败（可稍后手动上传）: {e}")
    else:
        print(f"[startup] 当前知识库文档数: {len(kb.list_documents())}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
