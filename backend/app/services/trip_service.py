"""
行程服务 —— 业务编排。

当前状态：
  generate_trip_itinerary() — 占位实现（等用户接 agent 层后替换）
  edit_trip_itinerary()     — 占位实现（同上）
"""
from datetime import date as DateType, timedelta
from app.models.schemas import (
    BudgetBreakdown, DayPlan, HotelItem, Itinerary, MealItem,
    SpotItem, TokenUsage, TransportItem,
    TripEditRequest, TripRequest,
)
from app.config import ENABLE_AMAP_ENRICHMENT
from app.services.map_service import enrich_itinerary_with_map_data


def _maybe_enrich(itinerary: Itinerary, city: str | None = None, budget: float | None = None) -> Itinerary:
    """按开关补充地图信息。"""
    if ENABLE_AMAP_ENRICHMENT:
        try:
            itinerary = enrich_itinerary_with_map_data(itinerary, city=city)
        except Exception:
            pass
    return itinerary


def generate_trip_itinerary(request: TripRequest) -> Itinerary:
    """生成完整 itinerary（当前为占位实现，等 agent 层替换）。

    用户接入步骤：
      1. 在 app/agents/ 下创建 trip_planner_agent.py
      2. 实现 plan_trip(request) -> Itinerary
      3. 把本函数的占位代码替换为调用 agent
    """
    day_count = (request.end_date - request.start_date).days + 1
    day_count = max(day_count, 1)
    days: list[DayPlan] = []

    for i in range(day_count):
        day_number = i + 1
        current_date = request.start_date + timedelta(days=i)
        spot_name = f"{request.destination} 推荐景点 {day_number}"
        days.append(DayPlan(
            day_index=day_number,
            date=current_date,
            theme=f"{request.destination} 第 {day_number} 天轻松游",
            spots=[SpotItem(
                name=spot_name,
                start_time="10:00", end_time="12:00",
                description="根据本地攻略和旅行偏好安排，适合用半天时间慢慢游览。",
                estimated_cost=50.0,
                location=request.destination,
            )],
            meals=[MealItem(
                name=f"{request.destination} 特色餐饮 {day_number}",
                meal_type="午餐",
                estimated_cost=80.0,
                notes="根据用户偏好和本地攻略预留的餐饮建议。",
            )],
            hotel=HotelItem(
                name=f"{request.destination} {request.hotel_level or '舒适型'}住宿 {day_number}",
                level=request.hotel_level or "舒适型",
                estimated_cost=400.0,
                location=f"{request.destination} 市区",
            ),
            transport=[TransportItem(
                mode="打车",
                from_place=f"{request.destination} 出发点",
                to_place=spot_name,
                estimated_cost=30.0,
                duration="30 分钟",
            )],
            notes=[f"当前旅行节奏：{request.pace or '适中'}", "今天以轻松游览为主。"],
        ))

    preference_text = "、".join(request.preferences) if request.preferences else "常规旅行体验"
    itinerary = Itinerary(
        trip_id=f"trip_{request.destination}_{request.start_date.isoformat()}",
        destination=request.destination,
        summary=f"这是一份为 {request.destination} 生成的 {day_count} 日行程，偏好重点为：{preference_text}。",
        days=days,
        estimated_budget=request.budget,
        budget_breakdown=BudgetBreakdown(
            transport=day_count * 30, hotel=day_count * 400,
            meals=day_count * 80, tickets=day_count * 50,
            other=request.budget * 0.05, total=request.budget,
        ),
        tips=[
            f"建议根据{request.destination}当天实时天气准备雨具或薄外套。",
            "古镇、生态廊道和石板路更适合慢慢走，鞋子尽量选择舒适防滑的款式。",
        ],
        source_notes=["[占位] Itinerary 由 trip_service 规则生成，待接入 agent。"],
        token_usage=TokenUsage(),
    )
    return _maybe_enrich(itinerary, city=request.destination, budget=request.budget)


def edit_trip_itinerary(request: TripEditRequest) -> Itinerary:
    """根据用户编辑指令返回更新后的 itinerary（占位）。"""
    updated = request.current_itinerary.model_copy(deep=True)
    updated.source_notes.append(f"已根据用户编辑指令更新行程：{request.user_instruction}")
    updated.tips.append("已根据你的修改要求更新目标日期，出发前建议再确认当天交通、天气和景点开放情况。")
    return _maybe_enrich(updated, city=updated.destination)
