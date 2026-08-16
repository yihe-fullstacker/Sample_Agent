"""
Coordinator 主 Agent - 核心协调者
负责与用户交互、收集婚礼信息、调用各 Subagent、生成最终方案
"""
"""
                    Coordinator Agent
                           │
              ┌────────────┼────────────┐
              ↓            ↓            ↓
        search_flights search_venues suggest_playlist
              ↓            ↓            ↓
        Travel Agent   Venue Agent   Playlist Agent
              ↓            ↓            ↓
            机票          场地          歌单

"""
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime #tool将普通python函数转换成LLM可以调用的tool。ToolRuntime提供 Tool 运行时的信息
from langchain.messages import HumanMessage #构造一条用户发的消息

from common.state import WeddingState #整个婚礼 Agent 系统的“共享记忆”
from common.tools import update_state
from common.model import get_model #导入模型

#Coordinator 不负责亲自查机票、找场地、查歌。它负责理解用户需求，然后把任务分发给专业 Subagent

#这个函数接收三个已经创建好的 Agent
#Coordinator 把三个已经存在的 Subagent 组合起来

# 为什么 Subagent 要作为参数传进来？外面创建好以后，传给 Coordinator
def create_coordinator(travel_agent, venue_agent, playlist_agent):
    """创建主 Coordinator Agent，把 Subagents 作为 Tools"""

    #把一个 Subagent 包装成 Coordinator 可以调用的 Tool
    @tool
    #Coordinator 调用 search_flights → search_flights 再调用 Travel Agent
    #定义一个异步 Tool,给 Coordinator 提供“搜索机票”的能力
    async def search_flights(runtime: ToolRuntime) -> str:
        #告诉 LLM：这个 Tool 是用来让 Travel Agent 查询婚礼目的地机票的
        """Travel agent searches for flights to the desired destination wedding location."""
        origin = runtime.state.get("origin", "")
        destination = runtime.state.get("destination", "")
        response = await travel_agent.ainvoke(
            {
                "messages": [
                    HumanMessage(content=f"Find flights from {origin} to {destination}")
                ]
            }
        )
        return response["messages"][-1].content
    #调用 Venue Agent 搜索婚礼场地
    @tool
    def search_venues(runtime: ToolRuntime) -> str:
        #告诉 LLM：这个 Tool 是用来让 Venue Agent 搜索婚礼目的地场地的
        """Venue agent chooses the best venue for the given location and capacity."""
        #获取用户输入的婚礼目的地
        destination = runtime.state.get("destination", "")
        #获取用户输入的婚礼人数
        capacity = runtime.state.get("guest_count", "")
        #构造查询任务
        query = f"Find wedding venues in {destination} for {capacity} guests"
        #调用 Venue Agent
        response = venue_agent.invoke(
            {"messages": [HumanMessage(content=query)]}
        )
        #返回结果
        return response["messages"][-1].content

    #调用 Playlist Agent
    @tool
    def suggest_playlist(runtime: ToolRuntime) -> str:
        #告诉 LLM：这个工具用于根据音乐类型生成婚礼歌单
        """Playlist agent curates the perfect playlist for the given genre."""
        #获取用户输入的音乐类型
        genre = runtime.state.get("genre", "")
        #生成查询任务
        query = f"Find {genre} tracks for wedding playlist"
        #调用 Playlist Agent
        response = playlist_agent.invoke(
            {"messages": [HumanMessage(content=query)]}
        )
        #返回结果
        return response["messages"][-1].content

    #创建 Coordinator Agent
#search_flights
#    ↓
#调用 Travel Agent
#
#search_venues
#    ↓
#调用 Venue Agent
#
#suggest_playlist   #update_state
#    ↓              #    ↓
#调用 Playlist Agent #修改 WeddingState
    coordinator = create_agent(
        model=get_model(),
        tools=[search_flights, search_venues, suggest_playlist, update_state],
        #这个 Coordinator 使用 WeddingState 作为状态结构
        state_schema=WeddingState,
        system_prompt="""
You are a wedding coordinator. Delegate tasks to your specialists for flights, venues and playlists.
First find all the information you need to update the state. Once that is done you can delegate the tasks.
Once you have received their answers, coordinate the perfect wedding for me.
""",
    )
    return coordinator
