"""星尘个人助手 - LangGraph Agent 实现

基于文档中的 ReAct 模式：
- MessagesState + add_messages
- LLM Node + Tool Node
- 条件边路由
- InMemorySaver 实现会话记忆
"""

# 定义 LangGraph 的 State、节点函数、构建图（StateGraph）、编译 app 的地方。是整个 Agent 的“大脑”。Graph + Nodes + State

from typing import Literal # 这个函数只能返回指定的几个值
from pathlib import Path # 处理文件路径

from langgraph.graph import StateGraph, START, END, MessagesState # 构建图的核心组件。MessagesState 是官方预定义的带消息列表的状态（自动用 add_messages 合并）。
from langgraph.prebuilt import ToolNode # 官方预置的工具执行节点，自动处理 tool_calls
from langgraph.checkpoint.memory import InMemorySaver # 内存版 Checkpointer，实现多轮对话记忆
from langchain_core.messages import SystemMessage # 消息类型
from langchain.chat_models import init_chat_model # 统一初始化各种 LLM（兼容 OpenAI 接口）

# 项目自己的模块（工具，配置，日志）
from agents.tools import ALL_TOOLS
from common.config import get_settings
from common.logger import setup_logger

# LLM → 判断是否调用工具 → 执行工具 → 把结果返回给 LLM → 继续推理 → 结束

# 创建日志记录器
logger = setup_logger("agents.assistant")
# 读取项目配置（模型名、API Key、温度等）
settings = get_settings()

# 读取系统提示词
PROMPT_PATH = Path(__file__).parent.parent / "resources" / "system_prompt.txt"
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else (
    "你是星尘，一位专业的个人智能助手。帮助用户管理日程、Todo和邮件。"
)

# 构建LLM 封装LLM 初始化，方便以后换模型。使用OpenAI兼容接口（很多国产模型都支持）
def _build_llm():
    """初始化 LLM（兼容 OpenAI 接口的任意模型，默认 DeepSeek）"""
    return init_chat_model(
        model=settings.llm_model,
        model_provider="openai",
        api_key=settings.openai_api_key or "sk-placeholder",
        base_url=settings.openai_api_base,
        temperature=settings.llm_temperature,
    )


# 创建图的函数  创建 LLM，并绑定工具（让 LLM 知道有哪些工具可以调用）
def create_assistant_graph():
    """构建并返回编译好的 LangGraph Agent"""
    llm = _build_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    # LLM节点（思考节点）
    def agent_node(state: MessagesState):
        """LLM 节点：思考并决定是否调用工具"""
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    # 条件边函数（路由判断）
    def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
        """条件边：有 tool_calls 则进入工具节点，否则结束"""
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "__end__"

    # 构建图
    # pyright/pycharm 对 langgraph 泛型的误报；运行时完全正常，这里显式忽略
    builder = StateGraph(MessagesState)  # type: ignore
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(ALL_TOOLS))

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", should_continue, {
        "tools": "tools",
        "__end__": END,
    })
    builder.add_edge("tools", "agent")  # 工具执行后回到 LLM，形成 ReAct 循环

    # 编译，启用 Checkpointer 实现跨轮记忆
    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    logger.info("PersonalAssistant Graph compiled successfully")
    return graph


# 全局单例模式
# 确保整个应用只创建一次图（单例），避免重复初始化 LLM 和编译
_graph = None


def get_assistant_graph():
    global _graph
    if _graph is None:
        _graph = create_assistant_graph()
    return _graph

# 作用：定义 Agent 的“大脑”和运行逻辑
# 它负责：
#
# 创建和配置 LLM
# 定义 LLM 节点（思考节点 agent_node）
# 定义 条件路由（should_continue）
# 构建 LangGraph 图（节点 + 边）
# 实现 ReAct 循环（LLM ↔ 工具）
# 加上 记忆（InMemorySaver）
# 提供获取图的单例方法
#
# 简单说：这是 控制流程 的代码。它决定“什么时候思考、什么时候调用工具、什么时候结束”。
