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
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init_table(conn: sqlite3.Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trips (
            trip_id   TEXT PRIMARY KEY,
            destination TEXT NOT NULL,
            days      INTEGER NOT NULL,
            summary   TEXT NOT NULL,
            itinerary TEXT NOT NULL
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