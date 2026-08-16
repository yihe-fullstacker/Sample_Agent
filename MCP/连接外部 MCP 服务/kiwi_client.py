import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

async def main():
    # 1. 连接 Kiwi MCP 服务器
    client = MultiServerMCPClient(
        {
            "kiwi-com-flight-search": {
                "transport": "http",
                "url": "https://mcp.kiwi.com"
            }
        }
    )

    # 2. 获取工具
    tools = await client.get_tools()

    # 3. 创建 Agent 并配置系统提示词
    agent = create_agent(
        model="deepseek-chat",
        tools=tools,
        system_prompt="You are a travel agent. Help user find best flights. No follow up questions. If the user uses Chinese, use zh-cn as the locale value."
    )

    # 4. 发起航班查询请求
    response = await agent.ainvoke({
        "messages": [HumanMessage("查一下2026年5月15日晚上从北京飞杭州的航班。")]
    })

    # 5. 打印结果
    for message in response["messages"]:
        message.pretty_print()

if __name__ == "__main__":
    asyncio.run(main())