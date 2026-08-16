# math_client.py
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

async def main():
    # 1. 连接本地自定义的 Math MCP 服务
    client = MultiServerMCPClient(
        {
            "math_service": {
                "transport": "stdio",
                "command": "python",
                "args": ["math_mcp_server.py"]
            }
        }
    )

    # 2. 获取数学工具
    tools = await client.get_tools()

    # 3. 创建数学助手 Agent
    agent = create_agent(
        model="deepseek-chat",
        tools=tools,
        system_prompt="You are a helpful agent. You must use tools to answer math questions."
    )

    # 4. 发起复杂的数学混合计算问题
    response = await agent.ainvoke({
        "messages": [HumanMessage("467和529的平方根之和是多少?")]
    })

    # 5. 打印交互过程
    for message in response["messages"]:
        message.pretty_print()

if __name__ == "__main__":
    asyncio.run(main())