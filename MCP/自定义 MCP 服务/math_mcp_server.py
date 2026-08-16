# math_mcp_server.py
from fastmcp import FastMCP

# 初始化 MCP 服务
mcp = FastMCP("Math")

# 定义加法工具
@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers"""
    return a + b

# 定义乘法工具
@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b

# 定义求平方根工具
@mcp.tool()
def square_root(x: float) -> float:
    """Calculate the square root of a number"""
    return x ** 0.5

# 设定通信方式并提供运行入口
if __name__ == "__main__":
    mcp.run(transport="stdio")