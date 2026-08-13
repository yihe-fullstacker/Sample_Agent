from typing import List, Optional #返回一个 SessionResponse 列表
from fastapi import APIRouter, HTTPException, Query
from Email_app.models.session import (
    SessionCreate,
    SessionResponse,
    get_sessions,
    create_session,
    delete_session
)
from Email_app.agents.email_agent import email_agent
#这块代码的作用：   把这些 Session 功能包装成 FastAPI HTTP 接口，让前端可以通过 API 操作会话

#创建一个 FastAPI 路由模块
router = APIRouter()

# 创建一个新的聊天会话
# response_model=SessionResponse 这个 API 返回的数据必须符合 SessionResponse 的结构
@router.post("/sessions", response_model=SessionResponse, tags=["会话"])
def create_new_session(session: SessionCreate):
    """创建新会话"""
    return create_session(session)

#获取会话列表
@router.get("/sessions", response_model=List[SessionResponse], tags=["会话"])
#支持两个查询参数
def list_sessions(
    user_id: Optional[str] = Query(None, description="用户ID"),
    biz_type: Optional[str] = Query(None, description="业务类型")
):
    """查询会话列表，支持按 user_id 和 biz_type 筛选"""
    return get_sessions(user_id=user_id, biz_type=biz_type)

#删除会话
@router.delete("/sessions/{thread_id}", tags=["会话"])
async def remove_session(thread_id: str):
    """删除会话及其checkpoint"""
    deleted = delete_session(thread_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    # 同步删除 LangGraph checkpoint 中的会话状态
    await email_agent.clear_messages(thread_id)
    return {"message": "Session deleted successfully"}

#获取历史消息
@router.get("/sessions/{thread_id}/messages", tags=["会话"])
async def get_session_messages(thread_id: str):
    """获取会话的历史消息"""
    try:
        result = await email_agent.get_messages(thread_id)
        return result
    except Exception as e:
        return {"messages": [], "error": str(e)}
