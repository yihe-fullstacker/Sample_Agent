"""Pydantic 请求/响应模型。"""
from typing import List, Optional
from pydantic import BaseModel, Field

# 这块代码的作用： 定义 API 的请求和响应数据模型（使用 Pydantic）。
# 它属于后端接口层，用来规范前端和后端之间传递的数据格式，同时自动做数据校验


# 单条聊天消息（角色 + 内容），用于多轮对话
class ChatMessage(BaseModel):
    role: str = Field(..., description="user | assistant | system")
    content: str

# 用户发送聊天请求时的数据结构（问题、会话ID、是否启用RAG）
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户问题")
    session_id: Optional[str] = Field(None, description="会话 ID，用于多轮")
    use_rag: bool = Field(True, description="是否启用知识库检索")

# 后端返回给前端的聊天结果（回答、来源、会话ID）
class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = Field(default_factory=list, description="检索到的知识片段摘要")
    session_id: str

# 单个文档的简要信息（用于列表展示）
class DocumentInfo(BaseModel):
    id: str
    filename: str
    chunks: int
    status: str = "indexed"

# 上传文件后的返回结果
class UploadResponse(BaseModel):
    success: bool
    message: str
    documents: List[DocumentInfo] = Field(default_factory=list)

# 知识库统计信息（文档数、块数等）
class KnowledgeStats(BaseModel):
    total_documents: int
    total_chunks: int
    collection_name: str

# 健康检查接口的返回结果（服务是否正常、模型是否就绪）
class HealthResponse(BaseModel):
    status: str
    embedding_ready: bool
    llm_ready: bool
