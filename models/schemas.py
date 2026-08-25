"""Pydantic models for request/response and agent state."""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

# 用 Pydantic 或 TypedDict 定义 State、请求/响应模型、分类结果等。EmailAgentState 类似的定义

# 聊天请求模型
# 作用：定义前端发给后端的聊天请求格式。
# message：用户输入的内容（必填）。
# thread_id：会话 ID（可选）。有它就能实现多轮对话记忆；没有就新建一个会话
class ChatRequest(BaseModel):
    message: str = Field(..., description="用户输入消息")
    thread_id: Optional[str] = Field(None, description="会话线程ID，用于记忆")

# 聊天响应模型
# 作用：定义后端返回给前端的聊天结果格式。
# reply：助手的回复内容。
# thread_id：当前会话 ID（方便前端下次继续用）。
# tool_calls：可选，记录本次调用了哪些工具（方便前端展示）
class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    tool_calls: Optional[List[str]] = None

# 日程模型
# 作用：定义「单条日程」的数据结构。
# 包含会议 ID、标题、开始时间、结束时间、地点
class ScheduleItem(BaseModel):
    id: str
    title: str
    start: str
    end: str
    location: str = ""

# 待办模型
# 作用：定义「单条待办事项」的结构。
# priority 只能是 high / medium / low 三个值之一。
# estimated_hours 默认 1 小时，done 默认未完成
class TodoItem(BaseModel):
    id: str
    title: str
    priority: Literal["high", "medium", "low"]
    due: str
    estimated_hours: float = 1.0
    done: bool = False

# 邮件模型
# 作用：定义「单封邮件」的结构。
# 包含发件人、主题、内容、时间、优先级、是否已读
class EmailItem(BaseModel):
    id: str
    sender: str
    subject: str
    content: str
    time: str
    priority: Literal["high", "medium", "low"] = "medium"
    read: bool = False

# 智能安排结果模型
# 作用：定义「安排明天工作」工具返回结果的完整结构。
# 包含日期、已有日程、推荐任务、检测到的冲突、调整建议和总结。
class ArrangeResult(BaseModel):
    date: str
    schedule: List[ScheduleItem]
    recommended_tasks: List[str]
    conflicts: List[str]
    suggestions: List[str]
    summary: str

# 健康检查响应模型
# 作用：定义 /health 接口的返回格式。
# 用于检查服务是否正常运行。
class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "PersonalAssistant"
    version: str = "1.0.0"


# Models 层就是项目的「数据说明书」，让所有层都清楚：
#
# 用户发来的消息长什么样
# 返回给用户的结果长什么样
# 日程、待办、邮件这些业务数据长什么样
#
# 定义清楚后，代码更安全、更易维护，也方便自动生成接口文档
