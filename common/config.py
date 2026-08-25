"""应用配置"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os
# 配置文件（API Key、模型名称、数据库连接、线程相关配置等）。

# 1. 应用基础信息
class Settings(BaseSettings):
    # pydantic v2 的标准写法：从 .env 读取，忽略多余字段
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "PersonalAssistant" #应用名称
    app_version: str = "1.0.0" #应用版本号
    debug: bool = True #是否开启调试模式(开发辅助功能，方便你排查问题和快速开发    )

    # LLM
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_api_base: str = os.getenv("OPENAI_API_BASE", "https://api.deepseek.com")
    llm_model: str = os.getenv("LLM_MODEL", "deepseek-chat")
    llm_temperature: float = 0.3

    # 服务
    host: str = "0.0.0.0"
    # 8000 被 KnowledgeBase_RAG 占用，个人助手使用 8010
    port: int = 8010

# 使用 @lru_cache() 做成单例，避免重复加载
@lru_cache()
def get_settings() -> Settings:
    return Settings()
