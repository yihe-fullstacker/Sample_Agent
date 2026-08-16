"""
LangGraph Server 图入口：婚礼策划 Multi-Agent

暴露模块级变量 graph：即 create_coordinator(...) 返回的 CompiledStateGraph。
创建顺序与 main.py 保持一致：travel_agent -> venue_agent -> playlist_agent -> coordinator。
"""

import asyncio
import sys
from pathlib import Path

# 将本文件所在目录置于 sys.path 最前面：
# - Marry-MultiAgent 路径含中文和连字符，不能假定可作为 Python 包名导入；
# - 必须放在最前，避免 venv 中的同名第三方包（common）遮蔽项目自身的 common 包。
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

# Windows 兼容：MCP stdio 子进程需要 Proactor 事件循环（与 main.py 一致）
if sys.platform == "win32" and not isinstance(
    asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy
):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from agents import (
    create_coordinator,
    create_playlist_agent,
    create_travel_agent,
    create_venue_agent,
)

# 持有 MCP client，避免其被垃圾回收后关闭会话
_mcp_client = None


async def _build_travel_agent():
    """创建 travel agent；失败时复用 main.py 的 MockTravel 回退逻辑"""
    global _mcp_client
    try:
        travel_agent, _mcp_client = await create_travel_agent()
        return travel_agent
    except Exception as e:
        print(f"[ERROR] travel agent 创建失败: {e}")
        print("将使用 mock travel_agent 继续演示流程...")

        from langchain_core.messages import AIMessage

        class MockTravel:
            @staticmethod
            async def ainvoke(_inputs):
                return {
                    "messages": [
                        AIMessage(
                            content="[Mock] Best flight: London LHR -> Paris CDG, €92, 1h15min, June 2026"
                        )
                    ]
                }

        _mcp_client = None
        return MockTravel()


travel_agent = asyncio.run(_build_travel_agent())
venue_agent = create_venue_agent()
playlist_agent = create_playlist_agent()
graph = create_coordinator(travel_agent, venue_agent, playlist_agent)
