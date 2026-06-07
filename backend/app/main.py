"""
旅游规划助手 — FastAPI 应用入口

路由一览：
  GET  /health            健康检查
  POST /trip/generate     生成旅行计划
  GET  /trip/history      历史记录列表
  GET  /trip/{trip_id}    查看单个行程
  DELETE /trip/{trip_id}  删除行程
"""
from fastapi import FastAPI, HTTPException
from app.schemas import TripGenerateRequest, TripPlan
from app.services.trip_service import generate_trip, get_history, get_detail, delete_trip

app = FastAPI(title="旅游规划助手 Backend MVP")


@app.get("/health")
def health():
    """健康检查——供前端/监控探活用，业务无关。"""
    return {"status": "所有检查都ok"}


@app.post("/trip/generate", response_model=TripPlan)
def create_trip(req: TripGenerateRequest):
    """生成旅行计划。
    req: 前端传来的 TripGenerateRequest（目的地、天数、人数、预算、偏好）
    返回: TripPlan（包含生成好的每日行程）
    """
    return generate_trip(req)


@app.get("/trip/history")
def history():
    """返回所有历史旅行计划列表，供用户查看/回溯。"""
    return get_history()


@app.get("/trip/{trip_id}", response_model=TripPlan)
def detail(trip_id: str):
    """根据 trip_id 查询单条旅行计划。"""
    return get_detail(trip_id)


@app.delete("/trip/{trip_id}")
def remove(trip_id: str):
    """根据 trip_id 删除旅行计划。"""
    return delete_trip(trip_id)
