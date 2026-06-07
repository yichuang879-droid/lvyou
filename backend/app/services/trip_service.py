from uuid import uuid4
from app.schemas import TripGenerateRequest, TripPlan, DailyPlan

from app.storage.memory_store import save_trip, list_trips



def generate_trip(req: TripGenerateRequest) -> TripPlan:
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
        trip_id=str(uuid4()),
        destination=req.destination,
        days=req.days,
        summary=f"这是一个{req.days}天的{req.destination}旅行计划。",
        itinerary=itinerary,
    )

    save_trip(plan)
    return plan

def get_history() -> list[TripPlan]:
    return list_trips()
