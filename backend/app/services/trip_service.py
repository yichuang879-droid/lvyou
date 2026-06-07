"""
行程服务 —— 核心业务逻辑。

当前骨架：
  generate_trip()  生成旅行计划（占位模版，后续接入 LLM）
  get_history()    获取全部历史行程
  get_detail()     按 ID 查询单条行程
  delete_trip()    删除指定行程
"""
from uuid import uuid4

from fastapi import HTTPException

from app.schemas import TripGenerateRequest, TripPlan, DailyPlan
from app.storage.memory_store import save_trip, list_trips, get_trip as _storage_get
from app.storage.memory_store import delete_trip as _storage_delete


def generate_trip(req: TripGenerateRequest) -> TripPlan:
    """根据用户请求生成一份旅行计划。

    当前为占位实现——生成为每一天的固定模版文字。
    后续步骤：
      1. 用 req 的字段拼成 prompt
      2. 调 LLM（DashScope / qwen-plus）
      3. 解析 LLM 返回的 JSON → TripPlan

    参数: req — Pydantic 校验后的请求体
    返回: TripPlan 对象（含 trip_id + 每日行程）
    """
    itinerary = []
    for i in range(1, req.days + 1):
        itinerary.append(
            DailyPlan(
                day=i,
                title=f"{req.destination}第{i}天行程",
                morning=f"上午游览{req.destination}代表性景点",
                afternoon=f"下午体验当地美食与街区",
                evening=f"晚上自由活动或夜景散步",
                tips=["注意根据天气调整安排", "提前确认景点开放时间"],
            )
        )

    plan = TripPlan(
        trip_id=str(uuid4()),   # 生成全局唯一 ID
        destination=req.destination,
        days=req.days,
        summary=f"这是一个{req.days}天的{req.destination}旅行计划。",
        itinerary=itinerary,
    )

    save_trip(plan)  # 持久化到 SQLite
    return plan


def get_history() -> list[TripPlan]:
    """返回所有历史旅行计划（最新在前）。"""
    return list_trips()


def get_detail(trip_id: str) -> TripPlan:
    """按 trip_id 查单条行程，不存在则抛 404。"""
    trip = _storage_get(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="行程不存在")
    return trip


def delete_trip(trip_id: str) -> dict:
    """按 trip_id 删除行程，不存在则抛 404。"""
    if not _storage_delete(trip_id):
        raise HTTPException(status_code=404, detail="要删除的行程不存在")
    return {"deleted": True}
