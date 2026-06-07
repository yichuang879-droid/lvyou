"""
旅游规划助手 — FastAPI 应用入口。

路由一览：
  GET  /health             健康检查
  POST /trip/generate      生成旅行计划
  GET  /trip               已保存行程列表
  GET  /trip/stats         Token 消耗统计
  POST /trip/save          保存行程
  GET  /trip/{trip_id}     查看单个行程
  DELETE /trip/{trip_id}   删除行程
  POST /trip/edit          编辑行程
  GET  /weather/forecast   天气预报
  GET  /export/{id}/markdown  导出 Markdown
  GET  /export/{id}/pdf       导出 PDF
  GET  /map/poi            高德 POI 搜索
  GET  /map/route          高德路径规划
"""
from fastapi import FastAPI
from app.api.routes.trip import router as trip_router
from app.api.routes.export import router as export_router
from app.api.routes.weather import router as weather_router
from app.api.routes.map import router as map_router

app = FastAPI(title="旅游规划助手 Backend MVP")

app.include_router(trip_router)
app.include_router(export_router)
app.include_router(weather_router)
app.include_router(map_router)


@app.get("/health")
def health():
    """健康检查——供前端/监控探活用，业务无关。"""
    return {"status": "所有检查都ok"}
