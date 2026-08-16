"""
Playlist Agent - 负责筛选婚礼歌单并计算预算
使用 SQLite (Chinook.db)
"""

#详细作用:
#创建一个 Playlist Agent，让 LLM 可以通过 query_playlist_db
# 工具查询 SQLite 数据库中的歌曲信息，然后根据婚礼音乐类型筛选歌曲，并计算总时长和预算

#LLM
# ↓
#调用 SQL Tool
# ↓
#查询数据库
# ↓
#分析查询结果
# ↓
#选择婚礼歌曲
# ↓
#计算总时长
#↓
#计算总价格

#如何把一个外部能力（SQLite 数据库）通过
# @tool 包装成 Agent 能调用的工具，然后让 LLM 自主生成 SQL、调用工具、根据结果继续推理，最终完成任务

from pathlib import Path

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_community.utilities import SQLDatabase

from common.model import get_model

# 数据库路径：项目根目录 resources/Chinook.db
DB_PATH = Path(__file__).resolve().parents[1] / "resources" / "Chinook.db"

# 确保 Chinook.db 存在   如果本地没有 Chinook.db，就自动下载一个
def _ensure_chinook_db() -> Path:
    """若 Chinook.db 不存在，则自动下载官方示例数据库"""
    if DB_PATH.exists():
        return DB_PATH

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    import urllib.request

    url = (
        "https://raw.githubusercontent.com/lerocha/chinook-database/master/"
        "ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"
    )
    print("[INFO] 本地未找到 Chinook.db，正在下载官方示例数据库 ...")
    try:
        urllib.request.urlretrieve(url, DB_PATH)
        print(f"[INFO] Chinook.db 已就绪: {DB_PATH}")
    except Exception as download_exc:
        raise FileNotFoundError(
            f"Chinook.db 下载失败: {download_exc}\n请手动下载后放到 {DB_PATH}"
        ) from download_exc
    return DB_PATH


def create_playlist_agent():
    """创建 playlist agent"""
    db_path = _ensure_chinook_db()
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
    #Agent与数据库之间的桥梁
    @tool
    def query_playlist_db(query: str) -> str:
        """Query the database for playlist information"""
        try:
            return db.run(query)
        except Exception as db_exc:
            return f"Error querying database: {db_exc}"

    # 简单测试
    print("[TEST] Playlist query:")
    try:
        print(query_playlist_db.invoke({"query": "SELECT * FROM Playlist LIMIT 5"}))
    except Exception as test_exc:
        print(f"[WARN] DB test failed: {test_exc}")

    playlist_agent = create_agent(
        model=get_model(),
        tools=[query_playlist_db],
        system_prompt="""
You are a playlist specialist. Query the sql database and curate the perfect playlist for a wedding given a genre.
Once you have your playlist, calculate the total duration and cost of the playlist, each song has an associated price.
If you run into errors when querying the database, try to fix them by making changes to the query.
Do not come back empty handed, keep trying to query the db until you find a list of songs.
You may need to make multiple queries to iteratively find the best options.
Note: Chinook DB has tables like Playlist, PlaylistTrack, Track, Genre, Artist, Album.
Track has Milliseconds for duration. You may invent reasonable prices if not present (e.g. $0.99 per track).
Prefer classic jazz tracks for the wedding atmosphere when the genre is jazz related.
""",
    )
    return playlist_agent
