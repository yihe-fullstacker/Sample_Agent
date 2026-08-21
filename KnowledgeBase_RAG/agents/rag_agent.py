"""Agentic RAG：LLM 自主决定是否调用知识库检索工具。"""
from __future__ import annotations

from typing import List, Optional

from langchain.tools import tool
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage

from common.config import CHAT_MODEL, DEFAULT_TOP_K
from db.vector_store import kb

# 用于评估/展示的上下文缓存（query -> contexts）
_contexts_store: dict = {}


@tool
def search_knowledge_base(query: str) -> str:
    """搜索个人知识库。当用户询问专业知识、笔记内容、文档相关问题时必须调用此工具。
    不要凭自己记忆回答知识库相关问题，必须先检索。
    """
    docs = kb.search(query, k=DEFAULT_TOP_K)
    if not docs:
        return "未在知识库中找到相关内容。"

    contexts = [d.page_content for d in docs]
    _contexts_store[query] = contexts

    parts = []
    for i, d in enumerate(docs, 1):
        src = d.metadata.get("source", "unknown")
        parts.append(f"[片段{i} | 来源:{src}]\n{d.page_content}")
    return "\n\n".join(parts)


SYSTEM_PROMPT = """你是一个个人知识库助手，名叫「知了」。

规则：
1. 涉及用户上传的笔记、文档、专业知识时，必须调用 search_knowledge_base 工具获取依据。
2. 禁止编造知识库中不存在的内容。检索无结果时明确告知「知识库中暂无相关信息」。
3. 回答简洁、准确，优先引用检索到的原文要点。
4. 普通闲聊（你好、谢谢等）可直接回复，无需检索。
5. 用中文回答。
"""


def build_agent():
    """创建 Agentic RAG Agent。"""
    agent = create_agent(
        model=CHAT_MODEL,
        tools=[search_knowledge_base],
        system_prompt=SYSTEM_PROMPT,
    )
    return agent


# 懒加载单例
_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


def chat(message: str, session_id: str = "default") -> tuple[str, List[str]]:
    """
    与 Agent 对话。
    返回 (answer, sources)。
    """
    agent = get_agent()
    # 清空本轮可能残留的 context（简单实现：按 query 存）
    prev = set(_contexts_store.keys())

    result = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        {"configurable": {"thread_id": session_id}},
    )

    answer = ""
    messages = result.get("messages", [])
    if messages:
        last = messages[-1]
        if isinstance(last, AIMessage):
            answer = last.content or ""
        elif hasattr(last, "content"):
            answer = str(last.content)
        else:
            answer = str(last)

    # 收集本轮新增的 contexts
    sources: List[str] = []
    for q, ctxs in _contexts_store.items():
        if q not in prev or q == message:
            sources.extend(ctxs[:3])  # 最多展示 3 条

    # 去重并截断过长
    uniq = []
    seen = set()
    for s in sources:
        key = s[:80]
        if key not in seen:
            seen.add(key)
            uniq.append(s[:300] + ("..." if len(s) > 300 else ""))
    return answer, uniq[:5]


def get_last_contexts(query: str) -> List[str]:
    return _contexts_store.get(query, [])
