"""
婚礼策划 Multi-Agent 系统入口
严格按照 PDF「第5节. 多Agent」Subagents 模式实现
"""

import sys
import asyncio
import os
from pathlib import Path

# Windows / Jupyter 兼容性修复
if sys.platform == "win32":
    if not isinstance(
        asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy
    ):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    if "ipykernel" in sys.modules:
        sys.stderr = sys.__stderr__

# 确保项目根目录（本文件所在目录）在 sys.path 中
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain.messages import HumanMessage


def _load_env():
    """从当前目录向上查找 .env 并加载（优先于系统环境变量）"""
    from dotenv import load_dotenv

    p = Path.cwd()
    for _ in range(6):
        if (p / ".env").exists():
            load_dotenv(dotenv_path=p / ".env", override=True)
            return
        p = p.parent
    load_dotenv()


_load_env()

from agents import (
    create_travel_agent,
    create_venue_agent,
    create_playlist_agent,
    create_coordinator,
)


async def main():
    print("=" * 60)
    print("婚礼策划 Multi-Agent 系统 (Subagents 模式)")
    print("=" * 60)

    # 检查必要环境变量
    if not os.getenv("DEEPSEEK_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        print("\n[WARNING] 未检测到 DEEPSEEK_API_KEY 或 OPENAI_API_KEY")
        print("请设置环境变量后重试，例如:")
        print("  export DEEPSEEK_API_KEY=sk-xxx")
        print("  或在 .env 文件中配置")
        print("\n代码结构已按分层方式完整实现，可直接在有密钥的环境中运行。")
        return

    if not os.getenv("TAVILY_API_KEY"):
        print("[WARNING] 未检测到 TAVILY_API_KEY，venue agent 可能失败")

    # 创建 subagents
    print("\n[1/4] 创建 travel agent (MCP Kiwi + Time)...")
    try:
        travel_agent, mcp_client = await create_travel_agent()
    except Exception as e:
        print(f"[ERROR] travel agent 创建失败: {e}")
        print("将使用 mock travel_agent 继续演示流程...")

        class MockTravel:
            @staticmethod
            async def ainvoke(_inputs):
                from langchain_core.messages import AIMessage
                return {
                    "messages": [
                        AIMessage(
                            content="[Mock] Best flight: London LHR -> Paris CDG, €92, 1h15min, June 2026"
                        )
                    ]
                }

        travel_agent = MockTravel()
        mcp_client = None

    print("\n[2/4] 创建 venue agent (Tavily)...")
    venue_agent = create_venue_agent()

    print("\n[3/4] 创建 playlist agent (SQLite Chinook)...")
    playlist_agent = create_playlist_agent()

    print("\n[4/4] 创建 Coordinator 主 Agent...")
    coordinator = create_coordinator(travel_agent, venue_agent, playlist_agent)

    # 测试用例（与 PDF 一致）
    print("\n" + "=" * 60)
    print("开始测试: 我来自伦敦，我想在巴黎举办一场100人的婚礼，爵士风格的")
    print("=" * 60 + "\n")

    response = await coordinator.ainvoke(
        {
            "messages": [
                HumanMessage(
                    content="我来自伦敦，我想在巴黎举办一场100人的婚礼，爵士风格的"
                )
            ],
        }
    )

    print("\n===== 完整对话轨迹 =====\n")
    for message in response["messages"]:
        message.pretty_print()

    if mcp_client:
        try:
            await mcp_client.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        # 在 Jupyter 等已有事件循环的环境中运行时，使用 nest_asyncio 嵌套运行
        try:
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.run(main())
        except ImportError:
            print("缺少 nest_asyncio，请在当前 Python 环境中执行: pip install nest_asyncio")
