"""
内存存储层 —— 基于 SQLite 持久化。

数据转换链路（对象 ⇄ 数据库）：
  存入: Pydantic对象 → .model_dump() → dict → json.dumps() → JSON字符串 → SQLite
  取出: SQLite → JSON字符串 → json.loads() → dict → DailyPlan(**dict) → Pydantic对象

每个请求获取独立连接，避免多线程竞争。
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Optional

from app.schemas import TripPlan, DailyPlan

# 数据库文件路径: backend/data/trips.db
DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DB_DIR / "trips.db"


def _get_conn() -> sqlite3.Connection:
    """创建数据库连接。
    - 自动创建 data 目录
    - row_factory=Row 使查询结果可用列名访问：row['trip_id']
    - WAL 模式允许并发读写，避免读写互相阻塞
    """
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init_table(conn: sqlite3.Connection):
    """建表（幂等——IF NOT EXISTS 保证重复执行不报错）。

    表结构:
      trip_id     TEXT PK — 行程唯一ID
      destination TEXT    — 目的地
      days        INTEGER — 天数
      summary     TEXT    — 摘要
      itinerary   TEXT    — 每日行程（JSON 字符串）
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trips (
            trip_id     TEXT PRIMARY KEY,
            destination TEXT NOT NULL,
            days        INTEGER NOT NULL,
            summary     TEXT NOT NULL,
            itinerary   TEXT NOT NULL
        )
        """
    )


def _row_to_trip(row: sqlite3.Row) -> TripPlan:
    """将数据库行转回 TripPlan 对象。
    1. json.loads 把 itinerary 字段从 JSON 字符串 → 字典列表
    2. 每个字典用 DailyPlan(**d) 重建对象
    """
    itinerary_raw = json.loads(row["itinerary"])
    return TripPlan(
        trip_id=row["trip_id"],
        destination=row["destination"],
        days=row["days"],
        summary=row["summary"],
        itinerary=[DailyPlan(**d) for d in itinerary_raw],
    )


# ─── CRUD 接口 ────────────────────────────────────────────

def save_trip(plan: TripPlan) -> TripPlan:
    """保存行程（INSERT OR REPLACE，同 ID 则覆盖）。"""
    conn = _get_conn()
    _init_table(conn)

    # 对象 → 字典 → JSON 字符串；ensure_ascii=False 保留中文
    itinerary_json = json.dumps(
        [d.model_dump() for d in plan.itinerary], ensure_ascii=False
    )

    conn.execute(
        "INSERT OR REPLACE INTO trips VALUES (?, ?, ?, ?, ?)",
        (plan.trip_id, plan.destination, plan.days, plan.summary, itinerary_json),
    )
    conn.commit()
    conn.close()
    return plan


def get_trip(trip_id: str) -> Optional[TripPlan]:
    """按 ID 查询单条行程，不存在返回 None。"""
    conn = _get_conn()
    _init_table(conn)
    row = conn.execute(
        "SELECT * FROM trips WHERE trip_id = ?", (trip_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_trip(row)


def list_trips() -> List[TripPlan]:
    """列出所有行程，最新创建的在最前。"""
    conn = _get_conn()
    _init_table(conn)
    rows = conn.execute("SELECT * FROM trips ORDER BY rowid DESC").fetchall()
    conn.close()
    return [_row_to_trip(r) for r in rows]


def delete_trip(trip_id: str) -> bool:
    """按 ID 删除行程，返回 True（删了）或 False（不存在）。"""
    conn = _get_conn()
    _init_table(conn)
    cursor = conn.execute("DELETE FROM trips WHERE trip_id = ?", (trip_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
