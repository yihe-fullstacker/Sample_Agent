"""
Venue Agent - 负责搜索婚礼场地
基于 Tavily 搜索
"""

from typing import Dict, Any

from langchain.agents import create_agent #负责创建Agent
from langchain.tools import tool #把一个普通的python函数变成Agent可以调用的Tool
from tavily import TavilyClient #导入搜索服务

from common.model import get_model


def create_venue_agent():
    """创建 venue agent"""
    # Tavily 搜索客户端
    tavily_client = TavilyClient()

    #加了@tool注解，将普通函数变成一个LangChain Agent 可以调用的Tool
    @tool
    def web_search(query: str) -> Dict[str, Any]:
        """Search the web for information"""
        return tavily_client.search(query)

    venue_agent = create_agent(
        model=get_model(),
        tools=[web_search],
        system_prompt="""
You are a venue specialist. Search for venues in the desired location, and with the desired capacity.
You are not allowed to ask any more follow up questions, you must find the best venue options based on the following criteria:
- Price (lowest)
- Capacity (exact match)
- Reviews (highest)
You may need to make multiple searches to iteratively find the best options.
""",
    )
    return venue_agent
