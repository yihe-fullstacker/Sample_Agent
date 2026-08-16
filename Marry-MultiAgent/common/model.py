"""
模型获取工具
"""

import os
from pathlib import Path

from dotenv import load_dotenv


def _load_env():
    """从当前目录向上查找 .env 并加载（优先于系统环境变量）"""
    p = Path.cwd()
    for _ in range(6):
        if (p / ".env").exists():
            load_dotenv(dotenv_path=p / ".env", override=True)
            return
        p = p.parent
    load_dotenv()


_load_env()


def get_model():
    """获取模型实例。优先 DeepSeek，兼容 OpenAI 兼容接口。"""
    try:
        from langchain_deepseek import ChatDeepSeek
        if os.getenv("DEEPSEEK_API_KEY"):
            return ChatDeepSeek(model="deepseek-chat", temperature=0.3)
    except Exception:
        pass

    from langchain_openai import ChatOpenAI

    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = (
        os.getenv("OPENAI_API_BASE")
        or os.getenv("DEEPSEEK_BASE_URL")
        or "https://api.deepseek.com/v1"
    )
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=api_key,
        base_url=base_url,
        temperature=0.3,
    )
