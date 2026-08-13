import json
from langchain.agents import AgentState, create_agent
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import HumanMessage, AIMessage #用户消息，AI消息
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Command #控制 LangGraph 恢复/更新
from langchain.messages import ToolMessage #Tool执行结果
from langchain.agents.middleware import wrap_model_call, dynamic_prompt, HumanInTheLoopMiddleware #人工确认
from langchain.agents.middleware import ModelRequest, ModelResponse
from typing import Callable
from Email_app.common.logger import logger
import aiosqlite #异步 SQLite
import os

AUTHENTICATED_KEY = "authenticated"


# state信息，记录用户是否授权邮箱操作
class AuthenticatedState(AgentState):
    authenticated: bool


# ==================== 1. 定义工具 ====================
# 定义工具，用于用户邮箱鉴权
#一般来说将工具类提取出来供Agent直接调用即可
@tool #LLM调用时需要提供括号里面的参数
def authenticate(email: str, password: str, runtime: ToolRuntime) -> Command:
    """Authenticate the user with the given email and password"""
    # 定义变量，记录校验结果
    authenticated = False
    message = "Authentication failed"
    # 校验邮箱和密码
    if email == "huge@itcast.cn" and password == "123":
        authenticated = True
        message = "Successfully authenticated"

    # 返回校验结果 告诉LangGraph“请更新 Agent 当前的 State“
    return Command(
        update={
            "authenticated": authenticated,
            "messages": [
                ToolMessage(message, tool_call_id=runtime.tool_call_id)
            ],
        }
    )


# 定义工具，用于操作邮箱
@tool
def check_inbox() -> str:
    """Read an email from the given address."""
    # 模拟收件箱邮件
    return [
        {
            "subject": "周末见个面？",
            "content": """
嗨 虎哥，
我下周会去城里，不知道我们有没有机会一起喝杯咖啡？
祝好，简
""",
            "from": "jane@itcast.cn",
            "status": "unread"
        },
        {
            "subject": "周五会议",
            "content": """
嗨 虎哥，
非常抱歉，我周五的会议无法准时参加了，能不能重新安排个时间？
祝好，小李
""",
            "from": "lixiaolong@itcast.cn",
            "status": "checked"
        }
    ]


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an response email"""
    return f"邮件已发送至 {to} , 主题： {subject} , 内容： {body}"


# 定义中间件，实现动态工具
#根据当前 Agent 的 State 中 authenticated 的值，动态决定本轮 LLM 可以使用哪些 Tool
@wrap_model_call
async def dynamic_tool_call(
        request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Allow read inbox and send email tools only if user provides correct email and password"""
    authenticated = request.state.get(AUTHENTICATED_KEY)
    if authenticated:
        tools = [check_inbox, send_email]
    else:
        tools = [authenticate]

    request = request.override(tools=tools)
    return await handler(request)


# 定义提示词
authenticated_prompt = "You are a helpful assistant that can check the inbox and send emails."
unauthenticated_prompt = """You are a helpful email assistant.
For system security protocols, you must authenticate user before any other
interaction.
"""


# 定义动态提示词中间件
#动态提示词中间件负责根据当前 State，判断这一次调用 LLM 时应该使用哪一个 Prompt
@dynamic_prompt
def dynamic_prompt_func(request: ModelRequest) -> str:
    """Generate system prompt based on authentication status"""
    authenticated = request.state.get(AUTHENTICATED_KEY)
    final_prompt = authenticated_prompt if authenticated else unauthenticated_prompt
    return final_prompt

#_serialize() 负责把后端 Agent 内部的数据“翻译”为前端能够接收的数据格式，是 Agent 后端与前端联调中的数据适配环节
# ==================== 辅助函数 ====================
def _serialize(obj):
    """递归转换对象为可 JSON 序列化的格式"""
    if hasattr(obj, 'value'):
        return _serialize(obj.value)
    elif hasattr(obj, 'model_dump'):
        return obj.model_dump()
    elif isinstance(obj, (list, tuple)):
        return [_serialize(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj

# 把前面学到的 SQLite Checkpointer、Agent、动态 Tool、动态 Prompt、HITL、SSE、
# 会话历史管理全部组装到一个 EmailAgent 类中，形成一个可以被 FastAPI 调用的完整 Email Agent 服务核心
class EmailAgent:
    def __init__(self):
        #准别三个变量
        self.conn: aiosqlite.Connection = None #准备数据库连接变量
        self.checkpointer: BaseCheckpointSaver = None #LangGraph 的 Checkpointer
        self.agent = None #真正创建Langchain Agent
#整个类的初始化入口，先准备数据库和 Checkpointer，再创建 Agent
    async def init(self):
        await self.init_checkpointer()
        logger.info("checkpointer 初始化完成 ....")
        await self.init_agent()
        logger.info("email agent 初始化完成 ....")
# 建立 SQLite 数据库，并把它交给 LangGraph Checkpointer
    async def init_checkpointer(self):
        # 建立连接
        os.makedirs("./db", exist_ok=True)
        self.conn = await aiosqlite.connect("./db/mail_fiend.db")
        logger.info("sqlite connection 完成 ....")
        # 初始化checkpointer
        self.checkpointer = AsyncSqliteSaver(conn=self.conn)
        # 自动建表 让Checkpointer 初始化自己的数据库表结构
        await self.checkpointer.setup()
#关闭SQLite
    async def close(self):
        await self.conn.close()
        logger.info("sqlite connection 关闭 ....")
#真正创建Agent
    async def init_agent(self):
        model_name = os.getenv("MODEL_NAME", "deepseek-chat")
        self.agent = create_agent(
            model_name,
            tools=[authenticate, check_inbox, send_email],
            state_schema=AuthenticatedState,
            checkpointer=self.checkpointer,
            middleware=[
                dynamic_tool_call, #根据认证状态决定 Agent 能使用哪些工具
                dynamic_prompt_func, #根据认证状态决定使用哪个 Prompt
                HumanInTheLoopMiddleware( #     决定哪些 Tool 执行前需要人工确认
                    interrupt_on={
                        "authenticate": False,
                        "check_inbox": False,
                        "send_email": True,
                    }
                )
            ],
        )
#运行 Agent，并把 Agent 的运行过程通过 SSE 持续发送给前端
#需要后端持续、实时地把 Agent 执行过程推送给前端”的场景，使用 generate_sse()方法
    # ==================== SSE 流式响应 ====================
    async def generate_sse(self, thread_id: str, message: str, interrupt_decision: dict):
        """生成 SSE 事件流"""
        #thread_id——找到对应Checkpoint——恢复State——继续对话
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        # 使用 HumanMessage 封装用户消息
        messages = {"messages": [HumanMessage(content=message)]}
        # 判断是消息还是 command
        _input = messages
        #用户确认 HITL
        if interrupt_decision:
            _input = Command(resume={
                "decisions": [interrupt_decision]
            })

        logger.info(f"调用agent，Input：{_input}")
        try:
            # 使用 astream 异步获取流式事件
            #异步流式运行 Agent
            async for chunk in self.agent.astream(
                    _input,
                    config=config,
                    stream_mode=["messages", "updates"], #同时获取两类信息，1.LLM 的流式输出,2.State/节点执行状态变化
                    version="v2"
            ):
                event_type = chunk["type"]
                data = chunk["data"]

                # 1. messages - LLM 流式输出（token 级别）
                if event_type == "messages":
                    token, metadata = data
                    content = None
                    if isinstance(token, AIMessage) and hasattr(token, "content"):
                        content = token.content
                    if content:
                        yield {
                            "event": "message",
                            "data": json.dumps(
                                {"type": "message", "content": content},
                                ensure_ascii=False
                            )
                        }
                # 2. updates - 节点完成的 state 更新
                elif event_type == "updates":
                    # 2a. 中断事件Agent 被 HITL 中断了
                    if "__interrupt__" in data:
                        interrupt_data = data['__interrupt__']
                        details = _serialize(interrupt_data)
                        # 把 LLM 输出发送给前端
                        yield {
                            "event": "interrupt",
                            "data": json.dumps(
                                {
                                    "type": "interrupt",
                                    "interrupt": {             #Agent现在暂停了，需要人工确认
                                        "reason": "需要人工确认",
                                        "details": details
                                    }
                                },
                                ensure_ascii=False, default=str
                            )
                        }
            # 无中断 → 流正常结束
            yield {
                "event": "done",
                "data": json.dumps({"type": "done", "content": "处理完成"}, ensure_ascii=False)
            }
        except Exception as e:
            logger.error(f"SSE 流中断: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"type": "error", "error": str(e)}, ensure_ascii=False)
            }
#根据 thread_id 从 Checkpointer 中恢复当前会话的 State，并把其中的消息返回给前端
    async def get_messages(self, thread_id: str) -> dict:
        """获取会话历史，如果存在中断则返回中断信息"""
        logger.info(f"获取历史消息，thread_id: {thread_id}")
        config = {"configurable": {"thread_id": thread_id}}
        state = await self.agent.aget_state(config)
        if state is None or not state.values:
            return {"messages": []}

        messages = state.values.get("messages", [])
        # 转换消息格式
        result = []
        for msg in messages:
            if not msg.content:
                continue
            if isinstance(msg, HumanMessage):
                result.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                result.append({"role": "assistant", "content": msg.content})

        response = {"messages": result}
        # 检查是否存在中断
        interrupts = None
        if hasattr(state, 'interrupts') and state.interrupts:
            interrupts = state.interrupts
        elif hasattr(state, 'tasks') and state.tasks:
            for task in state.tasks:
                if hasattr(task, 'interrupts') and task.interrupts:
                    interrupts = task.interrupts
                    break
        if interrupts:
            response["has_interrupt"] = True
            response["interrupt"] = {
                "reason": "需要人工确认",
                "details": _serialize(interrupts)
            }
        return response

    async def clear_messages(self, thread_id: str):
        """清空会话历史"""
        logger.info(f"清空历史消息，thread_id: {thread_id}")
        config = {"configurable": {"thread_id": thread_id}}
        try:
            # 兼容不同版本的 LangGraph 数据库清理
            if hasattr(self.checkpointer, 'adelete'):
                await self.checkpointer.adelete(config)
            else:
                await self.agent.aupdate_state(config, {"messages": []})
        except Exception as e:
            logger.error(f"清空会话失败: {e}")

#创建一个EmailAgent实例
email_agent = EmailAgent()
#当其他模块使用 from xxx import * 时，只暴露 email_agent,供外界调用
__all__ = ["email_agent"]
