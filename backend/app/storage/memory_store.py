import json
import sqlite3
from pathlib import Path
from typing import List, Optional
from app.schemas import TripPlan, DailyPlan

DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DB_DIR / "trips.db"


def _get_conn() -> sqlite3.Connection:
    """每个请求获取独立连接，避免线程安全问题。"""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row#以通过列名来访问数据，而不只是通过数字索引。row['trip_id'], row['destination']
    conn.execute("PRAGMA journal_mode=WAL")#默认情况下，SQLite 在写入时会锁定整个数据库文件，导致读被阻塞。WAL 模式允许读和写并发执行，大幅提升多线程/多请求场景下的性能，避免读写互相阻塞。
    return conn


def _init_table(conn: sqlite3.Connection):
    """
    初始化 trips 数据表。

    该函数通过传入的 SQLite 数据库连接对象 conn，执行 CREATE TABLE 语句。
    如果数据库中不存在名为 'trips' 的表，则创建它；
    如果表已存在，由于使用了 IF NOT EXISTS 子句，不会执行任何操作，也不会报错。

    参数:
        conn (sqlite3.Connection): 一个已打开的有效数据库连接。

    表结构说明:
        trip_id     TEXT PRIMARY KEY: 行程的唯一标识符，字符串类型，作为主键用于唯一确定一条记录。
        destination TEXT NOT NULL:    旅行目的地名称，例如"成都"、"上海"等，不允许为空。
        days        INTEGER NOT NULL: 行程总天数，整数类型，例如 3 表示 3 天，不允许为空。
        summary     TEXT NOT NULL:    行程的摘要描述文字，例如"成都3日游"，不允许为空。
        itinerary   TEXT NOT NULL:    详细的每日行程安排，以 JSON 格式的字符串存储，
                                       例如 '[{"day": 1, "title": "...", ...}]'，不允许为空。
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


def _row_to_trip(row) -> TripPlan:
    itinerary_raw = json.loads(row["itinerary"])
    return TripPlan(
        trip_id=row["trip_id"],
        destination=row["destination"],
        days=row["days"],
        summary=row["summary"],
        itinerary=[DailyPlan(**d) for d in itinerary_raw],
    )


def save_trip(plan: TripPlan) -> TripPlan:
    conn = _get_conn()
    _init_table(conn)
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
    conn = _get_conn()
    _init_table(conn)
    row = conn.execute("SELECT * FROM trips WHERE trip_id = ?", (trip_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_trip(row)


def list_trips() -> List[TripPlan]:
    conn = _get_conn()
    _init_table(conn)
    rows = conn.execute("SELECT * FROM trips ORDER BY rowid DESC").fetchall()
    conn.close()
    return [_row_to_trip(r) for r in rows]


def delete_trip(trip_id: str) -> bool:
    conn = _get_conn()
    _init_table(conn)
    cursor = conn.execute("DELETE FROM trips WHERE trip_id = ?", (trip_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted