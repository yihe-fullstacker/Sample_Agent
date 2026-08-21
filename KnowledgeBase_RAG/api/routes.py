"""FastAPI 路由。"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from models.schemas import (
    ChatRequest,
    ChatResponse,
    DocumentInfo,
    UploadResponse,
    KnowledgeStats,
    HealthResponse,
)
from common.config import UPLOADS_DIR, STATIC_DIR, DASHSCOPE_API_KEY, DEEPSEEK_API_KEY
from db.vector_store import kb
from agents.rag_agent import chat as agent_chat

"""
用 FastAPI 定义了一系列接口，让前端可以通过 HTTP 请求来：
上传文件 / 文本 → 入库
查询知识库状态和文档列表
进行聊天（支持 RAG）
清空知识库
提供前端页面
"""

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        embedding_ready=bool(DASHSCOPE_API_KEY),
        llm_ready=bool(DEEPSEEK_API_KEY),
    )


@router.get("/api/stats", response_model=KnowledgeStats)
async def stats():
    s = kb.stats()
    return KnowledgeStats(**s)


@router.get("/api/documents")
async def list_documents():
    return {"documents": kb.list_documents()}


@router.post("/api/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "文件名不能为空")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".md", ".txt", ".markdown", ".text"}:
        raise HTTPException(400, "仅支持 .md / .txt 文件")

    save_path = UPLOADS_DIR / f"{uuid.uuid4().hex}_{file.filename}"
    try:
        content = await file.read()
        save_path.write_bytes(content)
        doc_id, n_chunks = kb.add_file(save_path, filename=file.filename)
        return UploadResponse(
            success=True,
            message=f"已索引 {n_chunks} 个知识片段",
            documents=[
                DocumentInfo(id=doc_id, filename=file.filename, chunks=n_chunks, status="indexed")
            ],
        )
    except Exception as e:
        raise HTTPException(500, f"上传失败: {e}")


@router.post("/api/upload_text", response_model=UploadResponse)
async def upload_text(filename: str = Form("note.md"), content: str = Form(...)):
    if not content.strip():
        raise HTTPException(400, "内容不能为空")
    try:
        doc_id, n_chunks = kb.add_text(content, filename=filename)
        return UploadResponse(
            success=True,
            message=f"已索引 {n_chunks} 个知识片段",
            documents=[
                DocumentInfo(id=doc_id, filename=filename, chunks=n_chunks, status="indexed")
            ],
        )
    except Exception as e:
        raise HTTPException(500, f"添加失败: {e}")


@router.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    try:
        if not req.use_rag:
            # 简单直聊（不走 Agent 工具）
            from openai import OpenAI
            from common.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, CHAT_MODEL
            client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
            r = client.chat.completions.create(
                model=CHAT_MODEL,
                messages=[{"role": "user", "content": req.message}],
            )
            answer = r.choices[0].message.content or ""
            return ChatResponse(answer=answer, sources=[], session_id=session_id)

        answer, sources = agent_chat(req.message, session_id=session_id)
        return ChatResponse(answer=answer, sources=sources, session_id=session_id)
    except Exception as e:
        raise HTTPException(500, f"对话失败: {e}")


@router.delete("/api/knowledge")
async def clear_knowledge():
    kb.clear()
    return {"success": True, "message": "知识库已清空"}


# ---------- 前端静态页 ----------
@router.get("/")
async def index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(404, "前端页面未找到")
    return FileResponse(index_path)
