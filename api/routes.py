"""FastAPI 路由"""

# 导入必要的库和项目模块。
# 创建日志记录器。
# 创建 FastAPI 的路由器（router），后面所有接口都注册在它上面。
import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from models.schemas import ChatRequest, HealthResponse
from agents.assistant import get_assistant_graph
from common.logger import setup_logger

# from fastapi import FastAPI
#
# app = FastAPI()
# 有这个代表创建了FastAPI应用实例  app就是整个Web应用入口

# 定义具体的 API 路由（例如 /chat、/resume 等），接收用户问题，调用 agents 里的图。调用 Graph 的入口
logger = setup_logger("api.routes")
# 创建接口模块
router = APIRouter()


# 健康检查接口
# 作用：提供一个简单的健康检查接口（GET /health）。
# 用于判断服务是否正常运行（监控、负载均衡常用）。
@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()

# 非流式聊天接口
# 作用：提供普通的一次性聊天接口（POST /chat）。
# 流程：
# 获取编译好的图（get_assistant_graph()）
# 处理 thread_id（没有就新建一个，用于会话记忆）
# 调用 graph.invoke 运行 Agent
# 取出最后一条消息作为回复
# 返回结果 + thread_id（方便前端下次继续对话）
@router.post("/chat")
async def chat(req: ChatRequest):
    """非流式聊天接口（简单场景）"""
    graph = get_assistant_graph()
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(
        {"messages": [HumanMessage(content=req.message)]},
        config=config,
    )
    last_msg = result["messages"][-1]
    reply = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    return {
        "reply": reply,
        "thread_id": thread_id,
    }

# 流式聊天接口
# 作用：提供 SSE 流式接口（POST /chat/stream），推荐前端使用。
# 核心是 graph.astream_events，可以实时拿到：
# LLM 生成的每一个 token（打字机效果）
# 工具开始/结束的事件（前端可显示“正在查询日程...”）
#
# 通过 StreamingResponse 以 Server-Sent Events 格式推送给前端。
# 最后发送 done 事件，并带上 thread_id
@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """SSE 流式聊天接口（推荐前端使用）"""
    graph = get_assistant_graph()
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # 使用 astream_events 实现真正 token 级流式
            async for event in graph.astream_events(
                {"messages": [HumanMessage(content=req.message)]},
                config=config,
                version="v2",
            ):
                kind = event.get("event")
                if kind == "on_chat_model_stream":
                    chunk = event["data"].get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        payload = {
                            "type": "token",
                            "content": chunk.content,
                        }
                        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "tool")
                    payload = {"type": "tool_start", "name": tool_name}
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                elif kind == "on_tool_end":
                    payload = {"type": "tool_end"}
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

            # 结束标记
            yield f"data: {json.dumps({'type': 'done', 'thread_id': thread_id}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.exception("stream error")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

# 这块代码是 Agent 的对外入口，把内部的 LangGraph 图包装成 HTTP 接口，让前端或其他服务可以方便地调用
