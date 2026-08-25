"""个人助手工具集 - 基于 LangGraph Tool"""
from langchain.tools import tool
from typing import List
from db.mock_data import (
    MOCK_SCHEDULE, MOCK_TODOS, MOCK_EMAILS, get_tomorrow_date
)


# 定义 Agent 可用的工具（Tool），比如查天气、查日历、发消息等。Tool / Action 节点
@tool
def get_tomorrow_schedule() -> str:
    """获取明天的完整日程安排。返回时间、标题、地点。"""
    tomorrow = get_tomorrow_date()
    schedule = MOCK_SCHEDULE.get(tomorrow, [])
    if not schedule:
        return f"明天（{tomorrow}）没有任何日程安排。"
    lines = [f"明天（{tomorrow}）日程："]
    for s in schedule:
        lines.append(f"- {s['start']}-{s['end']}  {s['title']}  @ {s['location']}")
    return "\n".join(lines)


@tool
def get_todos(priority: str = "all") -> str:
    """获取待办事项列表。priority 可选值：all / high / medium / low。"""
    if priority == "all":
        todos = MOCK_TODOS
    else:
        todos = [t for t in MOCK_TODOS if t["priority"] == priority]
    if not todos:
        return f"没有优先级为 {priority} 的待办事项。"
    lines = ["待办事项："]
    for t in todos:
        status = "✅" if t.get("done") else "⬜"
        lines.append(
            f"- {status} [{t['priority'].upper()}] {t['title']} "
            f"(预估 {t['estimated_hours']}h, 截止 {t['due']})"
        )
    return "\n".join(lines)


@tool
def get_emails(unread_only: bool = True) -> str:
    """获取邮件列表。unread_only=True 时只返回未读邮件。"""
    emails = [e for e in MOCK_EMAILS if not e["read"]] if unread_only else MOCK_EMAILS
    if not emails:
        return "没有相关邮件。"
    lines = ["邮件列表："]
    for e in emails:
        flag = "🔴" if e["priority"] == "high" else "🟡" if e["priority"] == "medium" else "⚪"
        lines.append(
            f"- {flag} 来自 {e['sender']}\n"
            f"  主题：{e['subject']}\n"
            f"  内容：{e['content'][:80]}{'...' if len(e['content'])>80 else ''}\n"
            f"  时间：{e['time']}"
        )
    return "\n".join(lines)


@tool
def arrange_tomorrow_work() -> str:
    """
    核心能力：综合明天日程、高优先级 Todo、紧急邮件，
    生成智能工作安排，并检测冲突、给出调整建议。
    当用户说「安排明天」「看看冲突」「帮我规划明天」时优先调用此工具。
    """
    tomorrow = get_tomorrow_date()
    schedule = MOCK_SCHEDULE.get(tomorrow, [])
    high_todos = [t for t in MOCK_TODOS if t["priority"] == "high" and t["due"] <= tomorrow]
    urgent_emails = [e for e in MOCK_EMAILS if e["priority"] == "high" and not e["read"]]

    conflicts: List[str] = []
    suggestions: List[str] = []

    # 冲突检测逻辑
    morning_slots = [s for s in schedule if s["start"] < "12:00"]

    if morning_slots and (high_todos or urgent_emails):
        conflicts.append("上午会议密集，同时存在高优 Todo / 紧急邮件需要处理")
        suggestions.append("建议 08:30-09:20 优先处理紧急邮件与高优 Todo 碎片，或把部分报告工作提前到今晚")

    if len(schedule) >= 3 and high_todos:
        conflicts.append("全天会议较多，高优任务可能被挤压")
        suggestions.append("建议将「完成Q3报告初稿」拆分为上午碎片 + 下午15:40后连续完成")

    if urgent_emails:
        conflicts.append(f"存在 {len(urgent_emails)} 封紧急邮件未处理")
        suggestions.append("务必在 09:00 前完成紧急邮件回复，避免影响评审会")

    # 生成推荐安排
    plan_lines = [
        f"### 明天（{tomorrow}）智能工作安排",
        "",
        "#### 已有日程",
    ]
    for s in schedule:
        plan_lines.append(f"- **{s['start']}-{s['end']}**  {s['title']}  _{s['location']}_")

    plan_lines.extend([
        "",
        "#### 推荐任务插入时间线",
        "- **08:30 - 09:20**  处理紧急邮件 + 快速推进高优 Todo 碎片",
        "- **11:15 - 12:00**  继续 Q3 报告初稿（利用会议间隙）",
        "- **12:00 - 13:30**  午餐 + 休息（保持精力）",
        "- **15:40 - 17:00**  完成剩余高优任务 + 代码 Review",
        "- **17:00 - 17:30**  整理明日待办与邮件收尾",
    ])

    if conflicts:
        plan_lines.append("")
        plan_lines.append("#### ⚠️ 检测到的冲突")
        for c in conflicts:
            plan_lines.append(f"- {c}")
        plan_lines.append("")
        plan_lines.append("#### 💡 调整建议")
        for s in suggestions:
            plan_lines.append(f"- {s}")
    else:
        plan_lines.append("")
        plan_lines.append("✅ 当前日程与任务无明显硬冲突，可按推荐时间线执行。")

    plan_lines.extend([
        "",
        "#### 今日高优 Todo 提醒",
    ])
    for t in high_todos:
        plan_lines.append(f"- [{t['priority'].upper()}] {t['title']}（预估 {t['estimated_hours']}h）")

    return "\n".join(plan_lines)

# ALL_TOOLS 就是一个工具清单，把所有可用工具收集起来，方便一次性交给 LLM 和 ToolNode 使用。这是标准且推荐的写法
ALL_TOOLS = [get_tomorrow_schedule, get_todos, get_emails, arrange_tomorrow_work]

# 作用：定义 Agent 能使用的“工具/技能”
# 它负责：
#
# 用 @tool 装饰器定义具体功能函数
# 每个函数对应一个可被 LLM 调用的工具
# 目前实现了 4 个工具：
# get_tomorrow_schedule：查明天日程
# get_todos：查待办事项
# get_emails：查邮件
# arrange_tomorrow_work：智能规划明天工作（核心能力）
#
# 最后把所有工具收集到 ALL_TOOLS 列表里，供第一块代码使用
#
# 简单说：这是 能力实现 的代码。它告诉 Agent “我有哪些本事可以调用”。
