from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from Email_app.models.schemas import ChatRequest
from Email_app.agents.email_agent import email_agent
#FastAPI接口层

#作用：FastAPI 的这几个接口，就像“窗口”；前端通过窗口把请求送进 EmailAgent，Agent 执行完以后，再通过 SSE 把结果送回前端

#创建一个路由器：把和聊天相关的 API 集中管理
router = APIRouter()

#这一块负责：前端怎么调用 Agent

#接收用户消息 → 调用 EmailAgent → Agent 流式运行 → SSE 返回
@router.post("/chat/stream")
async def chat_endpoint(request: ChatRequest):
    """发送聊天消息，使用 SSE 流式返回 Agent 响应（与 /chat/send 一致）。"""
    return EventSourceResponse(
        email_agent.generate_sse(
            request.thread_id,
            request.message or "",
            request.interrupt_decision
        )
    )

#接收用户消息 → 调用 EmailAgent → Agent 流式运行 → SSE 返回 → 处理 HITL
@router.post("/chat/send", tags=["聊天"])
async def send_chat(request: ChatRequest):
    """发送聊天消息，使用 SSE 流式返回 Agent 响应。同时处理 HITL 中断决策。"""
    return EventSourceResponse(
        email_agent.generate_sse(
            request.thread_id,
            request.message or "",
            request.interrupt_decision
        )
    )

#根据 thread_id 获取这个聊天会话以前的消息
@router.get("/chat/messages")
async def get_chat_messages(thread_id: str):
    """获取历史消息"""
    result = await email_agent.get_messages(thread_id)
    return result

#删除 thread_id 对应的聊天历史
@router.delete("/chat/messages")
async def clear_chat_messages(thread_id: str):
    """清空历史消息"""
    await email_agent.clear_messages(thread_id)
    return {"success": True}
