"""
公共 Tools
"""

from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage
from langgraph.types import Command


@tool
def update_state(
    origin: str,
    destination: str,
    guest_count: str,
    genre: str,
    runtime: ToolRuntime,
) -> str:
    """Update the state when you know all of the values: origin, destination, guest_count, genre"""
    return Command(
        update={
            "origin": origin,
            "destination": destination,
            "guest_count": guest_count,
            "genre": genre,
            "messages": [
                ToolMessage(
                    "Successfully updated state",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
