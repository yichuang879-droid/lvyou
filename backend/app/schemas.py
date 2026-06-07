"""
Pydantic 数据模型 —— 定义请求/响应的"形状"，兼做数据校验。

三个模型：
  TripGenerateRequest  前端 POST 请求体
  DailyPlan            每一天的行程结构
  TripPlan             完整旅行计划（接口返回给前端）
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class TripGenerateRequest(BaseModel):
    """POST /trip/generate 的请求体格式。
    Field(...)         → 必填字段
    Field(..., ge=N)   → 必填 + 数值下限
    Optional[int]=None → 可选字段，不传则为 None
    """
    destination: str = Field(..., examples=["成都"])   # 目的地，如"成都"
    start_date: date                                     # 出发日期
    days: int = Field(..., ge=1, le=30)                  # 行程天数（1-30）
    people: int = Field(..., ge=1)                       # 出行人数
    budget: Optional[int] = None                         # 预算（可选）
    preferences: List[str] = []                          # 偏好标签，如["美食","户外"]


class DailyPlan(BaseModel):
    """单日行程结构。所有字段必填，tips 默认空列表。"""
    day: int              # 第几天（1-based）
    title: str            # 当日主题，如"成都第1天行程"
    morning: str          # 上午安排
    afternoon: str        # 下午安排
    evening: str          # 晚上安排
    tips: List[str] = []  # 小贴士列表


class TripPlan(BaseModel):
    """完整的旅行计划，作为 API 返回值。"""
    trip_id: str               # 唯一标识（UUID4）
    destination: str           # 目的地
    days: int                  # 总天数
    summary: str               # 摘要描述
    itinerary: List[DailyPlan] # 每日行程列表
