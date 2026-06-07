from fastapi import APIRouter, Query

from app.services.map_service import search_poi, get_route

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/poi")
def poi(
    keyword: str = Query(..., description="地点关键词，例如：宽窄巷子"),
    city: str = Query(..., description="城市，例如：成都"),
):
    return search_poi(keyword=keyword, city=city)

@router.get("/route")
def route(
    origin: str = Query(..., description="起点经纬度，例如：104.0668,30.5728"),
    destination: str = Query(..., description="终点经纬度，例如：104.0800,30.6600"),
):
    return get_route(origin=origin, destination=destination)