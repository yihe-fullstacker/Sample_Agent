from .assistant import get_assistant_graph
# 核心业务逻辑层。放 Agent 本身的实现代码。图的定义、节点函数、路由逻辑
# Agent 层就是专门用来干这个的
# 它的核心职责就是：
# 定义 State（这里用的是官方的 MessagesState）
# 编写 节点函数（agent_node）
# 定义 路由逻辑（should_continue 条件边）
# 构建 图（StateGraph）
# 编译图并加上 Checkpointer（实现记忆）
# 对外提供获取图的方法（get_assistant_graph）