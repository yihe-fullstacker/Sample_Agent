"""
Travel Agent - 负责查询机票
使用 Time 和 Kiwi 两个 MCP 服务
"""

import os
import sys

from langchain.agents import create_agent #创建Agent
from langchain_mcp_adapters.client import MultiServerMCPClient #同时连接多个 MCP Server，并把这些 MCP Server 提供的工具拿回来，交给 Agent 使用

from common.model import get_model


async def create_travel_agent():
    """创建 travel agent (需要 MCP)"""
    # Kiwi MCP 服务绕过本地代理（修复: 本地代理会断开 streamable HTTP 连接）
    _noproxy = os.environ.get("NO_PROXY", "")
    if "mcp.kiwi.com" not in _noproxy:
        _noproxy = (_noproxy.strip(",") + ",mcp.kiwi.com").strip(",")
        os.environ["NO_PROXY"] = _noproxy
        os.environ["no_proxy"] = _noproxy
    #建立 MCP Server 的连接配置
    client = MultiServerMCPClient(
        {
            #机票 MCP
            "travel_server": {
                "transport": "http",
                "url": "https://mcp.kiwi.com",
            },
            #时间 MCP
            "time": {
                "transport": "stdio",
                # 直接使用当前 Python 环境启动 mcp-server-time（uvx 可能解析到不兼容的 mcp 2.x）
                "command": sys.executable,
                "args": [
                    "-m", "mcp_server_time",
                    "--local-timezone=Asia/Shanghai",
                ],
            },
        }
    )
    #获取所有 MCP Tools
    tools = await client.get_tools()
    #打印所有 MCP Tools名称
    print(f"[INFO] Travel MCP tools loaded: {[t.name for t in tools]}")

    #创建 Travel Agent
    travel_agent = create_agent(
        model=get_model(),
        #把刚刚从 MCP 获取的工具交给 Agent
        tools=tools,
        #设定提示词 让 Agent 按三个维度考虑
        system_prompt="""
You are a travel agent. Search for flights to the desired destination wedding location, you must call tool to get current time.
You are not allowed to ask any more follow up questions, you must find the best flight options based on the following criteria:
- Price (lowest, economy class)
- Duration (shortest)
- Date (time of year which you believe is best for a wedding at this location)
To make things easy, only look for one ticket, one way.
You may need to make multiple searches to iteratively find the best options.
You will be given no extra information, only the origin and destination. It is your job to think critically about the best options.
Once you have found the best options, let the user know your shortlist of options.
Remember call tool to get current time when you need.
""",
    )
    #create_xxx() 负责创建对象，return 把对象交给外部，外部拿到后就一直复用这些对象
    return travel_agent, client
