import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel

#FastAPI 路由层负责接收 HTTP 请求，而 session.py 负责真正操作数据库

#作用：它负责管理 EmailAgent 项目中的“会话（Session）”，
# 把每个用户创建的聊天会话保存到 SQLite 数据库中，并提供创建、查询、删除会话的功能。

#① 定义数据格式
#        ↓
#② 连接 SQLite 数据库
#        ↓
#③ 创建/查询/删除会话
#        ↓
#④ 程序启动时自动创建数据库表

# Pydantic 模型 定义“创建会话”需要什么数据
class SessionCreate(BaseModel):
    """创建会话的请求模型"""
    user_id: str
    biz_type: str
    name: str

#返回给前端的数据
class SessionResponse(BaseModel):
    """会话响应模型"""
    thread_id: str
    user_id: str
    biz_type: str
    name: str
    created_at: str
    updated_at: str


# 数据库配置
#Email_app/db/sessions.db，指定 SQLite 数据库文件的位置
DB_PATH = Path(__file__).parent.parent / "db/sessions.db"

#每次需要操作数据库的时候,创建一个 SQLite 连接
def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

#创建数据库表
def init_db():
    """初始化数据库，创建 sessions 表"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        thread_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        biz_type TEXT NOT NULL,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

#创建会话,整个文件的核心函数
def create_session(session: SessionCreate) -> SessionResponse:
    """创建新会话"""
    #连接数据库
    conn = get_db_connection()
    cursor = conn.cursor()
    #生成唯一的 thread_id
    thread_id = str(uuid.uuid4())
    #生成当前时间
    now = datetime.now().isoformat()
    #把数据写进 SQLite
    cursor.execute(
        """
        INSERT INTO sessions (thread_id, user_id, biz_type, name, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (thread_id, session.user_id, session.biz_type, session.name, now, now)
    )
    #正式保存到数据库
    conn.commit()
    #关闭数据库
    conn.close()
    return SessionResponse(
        thread_id=thread_id,
        user_id=session.user_id,
        biz_type=session.biz_type,
        name=session.name,
        created_at=now,
        updated_at=now
    )

#从数据库中把会话列表查询出来
def get_sessions(user_id: Optional[str] = None, biz_type: Optional[str] = None) -> List[SessionResponse]:
    """查询会话列表，支持按 user_id 和 biz_type 筛选"""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT thread_id, user_id, biz_type, name, created_at, updated_at FROM sessions"
    params = []
    conditions = []
    #根据用户查询
    if user_id:
        conditions.append("user_id = ?")
        params.append(user_id)
    #根据业务类型查询
    if biz_type:
        conditions.append("biz_type = ?")
        params.append(biz_type)
    #两个条件一起查询
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    #按照最后更新时间倒序排列
    query += " ORDER BY updated_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [
        SessionResponse(
            thread_id=row["thread_id"],
            user_id=row["user_id"],
            biz_type=row["biz_type"],
            name=row["name"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
        for row in rows
    ]

#为什么使用bool，如果成功删除是否，返回True/False
def delete_session(thread_id: str) -> bool:
    """删除会话"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE thread_id = ?", (thread_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# 初始化数据库
init_db()