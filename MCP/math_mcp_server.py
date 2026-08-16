# 此单元格执行后，会在当前目录下自动生成 "math_mcp_server.py" 文件
# 注意：%%writefile 只负责把下面的代码写入文件，不会执行这些代码。
# 这个 MCP Server 由后面的“连接本地自定义 Math MCP”单元以子进程方式自动启动，
# 不要在 Jupyter 里直接运行 mcp.run(...)，否则会报 "Already running asyncio" 错误。

# 这一整块代码的作用：创建了一个最简单的 MCP Server，并向外提供 3 个数学工具：
# 加法、乘法、平方根。其他 MCP Client / Agent 可以连接这个 Server，然后调用这些工具。

# FastMCP 理解成：帮助我们快速创建 MCP Server 的工具类
from fastmcp import FastMCP

# 初始化并命名 MCP 服务
mcp = FastMCP("Math")

# 注册加法工具
@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers"""
    return a + b

# 注册乘法工具
@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b

# 注册平方根计算工具
@mcp.tool()
def square_root(x: float) -> float:
    """Calculate the square root of a number"""
    return x ** 0.5

# 启动 MCP Server，并使用 stdio 作为通信方式
if __name__ == "__main__":
    # 通过 `python math_mcp_server.py` 以子进程方式运行时 __file__ 存在，正常启动服务；
    # 若直接在 Jupyter 单元格里执行，则只提示、不启动，避免 "Already running asyncio" 报错。
    if "__file__" in globals():
        mcp.run(transport="stdio")
    else:
        print("提示: 正在 Jupyter 中直接执行，stdio MCP 服务由客户端单元自动以子进程方式启动，无需在此启动。")

