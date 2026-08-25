"""模拟日程、Todo、邮件数据（真实环境可替换为数据库/API）"""
from datetime import datetime, timedelta
from typing import List, Dict
# 目前用假数据模拟（用户信息、历史对话、知识库等），后期可换成真实数据库。外部数据源


# 工具函数  调用会使用这些数据
# 作用：获取明天的日期（格式：YYYY-MM-DD）。
# 被后面的模拟数据和工具函数使用，保证“明天”的数据是动态的

# 这里定义 get_tomorrow_date 是为了方便地、动态地获取明天的日期，供模拟数据和工具函数重复使用，而不是给 LLM 调用的工具
def get_tomorrow_date() -> str:
    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

# 模拟日程数据
# 作用：模拟用户明天的日程安排。
# 结构是「日期 → 会议列表」。
# 被 get_tomorrow_schedule 和 arrange_tomorrow_work 工具使用
MOCK_SCHEDULE: Dict[str, List[dict]] = {
    get_tomorrow_date(): [
        {"id": "m1", "title": "产品评审会", "start": "09:30", "end": "11:00", "location": "会议室A"},
        {"id": "m2", "title": "客户演示", "start": "14:00", "end": "15:30", "location": "线上Zoom"},
        {"id": "m3", "title": "团队周会", "start": "16:00", "end": "17:00", "location": "会议室B"},
    ]
}

# 模拟待办数据
# 作用：模拟用户的待办事项列表。
# 包含优先级、截止日期、预估时间、是否完成等信息。
# 被 get_todos 和 arrange_tomorrow_work 工具使用
MOCK_TODOS: List[dict] = [
    {"id": "t1", "title": "完成Q3报告初稿", "priority": "high", "due": get_tomorrow_date(), "estimated_hours": 3.0, "done": False},
    {"id": "t2", "title": "回复合作伙伴邮件", "priority": "medium", "due": get_tomorrow_date(), "estimated_hours": 1.0, "done": False},
    {"id": "t3", "title": "代码Review PR#128", "priority": "high", "due": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"), "estimated_hours": 2.0, "done": False},
    {"id": "t4", "title": "准备下周培训材料", "priority": "low", "due": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"), "estimated_hours": 4.0, "done": False},
    {"id": "t5", "title": "更新项目文档", "priority": "medium", "due": get_tomorrow_date(), "estimated_hours": 1.5, "done": False},
]

# 模拟邮件数据
# 作用：模拟用户的邮件列表。
# 包含发件人、主题、内容、优先级、是否已读等信息。
# 被 get_emails 和 arrange_tomorrow_work 工具使用
MOCK_EMAILS: List[dict] = [
    {
        "id": "e1",
        "sender": "boss@company.com",
        "subject": "紧急：明天上午需要你的数据支持",
        "content": "小王，明天上午10点前把最新销售数据发我，评审会要用。请务必优先处理。",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "priority": "high",
        "read": False
    },
    {
        "id": "e2",
        "sender": "partner@external.com",
        "subject": "合作方案确认",
        "content": "请在明天中午前确认方案细节并回复，我们好推进下一步。",
        "time": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
        "priority": "medium",
        "read": False
    },
    {
        "id": "e3",
        "sender": "hr@company.com",
        "subject": "下周团建活动通知",
        "content": "下周五下午团建，请确认是否参加。",
        "time": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
        "priority": "low",
        "read": True
    },
]

# db 层负责什么？
# db 层 = 数据访问层（Data Access Layer）
# 它的职责是：
#
# 提供 Agent 需要的外部数据
# 目前用模拟数据（Mock）代替真实数据库
# 真实项目中，这里会改成：
# 连接数据库（MySQL、PostgreSQL、MongoDB 等）
# 调用外部 API（日历 API、邮件 API、Todo 服务等）
# 读写真实数据