"""应用配置：从环境变量加载 API Key 等。"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
RESOURCES_DIR = BASE_DIR / "resources"
UPLOADS_DIR = BASE_DIR / "uploads"
DB_DIR = BASE_DIR / "db_data"
STATIC_DIR = BASE_DIR / "static"

# 确保目录存在
for d in (RESOURCES_DIR, UPLOADS_DIR, DB_DIR):
    d.mkdir(parents=True, exist_ok=True)

# LLM / Embedding
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# 模型名
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")
CHAT_MODEL = os.getenv("CHAT_MODEL", "deepseek-chat")

# 检索参数
DEFAULT_TOP_K = 5
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Chroma 持久化路径
CHROMA_PERSIST_DIR = str(DB_DIR / "chroma_kb")
COLLECTION_NAME = "personal_knowledge_base"
