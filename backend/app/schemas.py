from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class TripGenerateRequest(BaseModel):
    destination: str = Field(..., examples=["成都"])
    start_date: date
    days: int = Field(..., ge=1, le=30)
    people: int = Field(..., ge=1)
    budget: Optional[int] = None
    preferences: List[str] = []


class DailyPlan(BaseModel):
    day: int
    title: str
    morning: str
    afternoon: str
    evening: str
    tips: List[str] = []


class TripPlan(BaseModel):
    trip_id: str
    destination: str
    days: int
    summary: str
    itinerary: List[DailyPlan]