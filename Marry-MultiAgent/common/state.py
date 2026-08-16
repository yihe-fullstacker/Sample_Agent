"""
婚礼状态定义 (WeddingState)
"""

from typing_extensions import NotRequired

from langchain.agents import AgentState


class WeddingState(AgentState):
    """记录婚礼相关信息的状态"""
    origin: NotRequired[str]          # 出发地
    destination: NotRequired[str]     # 婚礼举办地
    guest_count: NotRequired[str]     # 宾客人数
    genre: NotRequired[str]           # 音乐风格
