import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage


async def main():
    # 1. 建立并连接 Time MCP 服务器
    client = MultiServerMCPClient(
        {
            "time": {
                "transport": "stdio",
                "command": "uvx",
                "args": [
                    "mcp-server-time",
                    "--local-timezone=Asia/Shanghai"
                ]
            }
        }
    )

    # 2. 获取 MCP 服务提供的工具 (注意：此步骤为异步操作，需要 await)
    tools = await client.get_tools()

    # 打印获取到的工具信息
    print("--- 已获取的工具 ---")
    for tool in tools:
        print(f"工具名称: {tool.name}")
        print(f"描述: {tool.description}")
        print("-" * 20)

    # 3. 创建 Agent 并绑定获取到的工具
    agent = create_agent("deepseek-chat", tools)

    # 4. 调用 Agent 进行测试
    response = await agent.ainvoke({
        "messages": [HumanMessage("现在几点了？")]
    })

    # 5. 打印执行结果
    print("\n--- 运行结果 ---")
    for message in response["messages"]:
        message.pretty_print()


if __name__ == "__main__":
    asyncio.run(main())