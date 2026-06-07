"""地图服务 —— 高德 POI 搜索 + 地理编码 + 路径规划 + 行程补全。"""
from __future__ import annotations
import logging
from typing import Any
import httpx
from app.config import (
    AMAP_API_KEY, AMAP_BASE_URL, AMAP_TIMEOUT_SECONDS, AMAP_DEFAULT_CITY, REDIS_MAP_TTL_SECONDS,
)
from app.models.schemas import Itinerary, SpotItem, HotelItem, TransportItem
from app.services.cache_service import get_cached_json, set_cached_json

logger = logging.getLogger(__name__)


def _ensure_key() -> None:
    if not AMAP_API_KEY:
        raise RuntimeError("当前环境未配置 AMAP_API_KEY，无法调用高德地图服务。")


def _request_amap(path: str, params: dict[str, Any]) -> dict[str, Any]:
    _ensure_key()
    with httpx.Client(timeout=AMAP_TIMEOUT_SECONDS) as client:
        resp = client.get(f"{AMAP_BASE_URL}{path}", params={"key": AMAP_API_KEY, **params})
        resp.raise_for_status()
        payload = resp.json()
    if payload.get("status") != "1":
        raise RuntimeError(f"高德地图接口调用失败：{payload.get('info', '未知错误')}")
    return payload


def _parse_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _split_location(location: str | None) -> tuple[float | None, float | None]:
    if not location or "," not in location:
        return None, None
    lng_text, lat_text = location.split(",", 1)
    return _parse_float(lat_text), _parse_float(lng_text)


def _normalize_cache_text(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip().lower()


# ─── 公开 API ────────────────────────────────────────────

def geocode_address(address: str, city: str | None = None) -> dict[str, Any] | None:
    """根据地址获取经纬度信息。"""
    cache_key = f"map:geocode:{_normalize_cache_text(address)}:{_normalize_cache_text(city or AMAP_DEFAULT_CITY)}"
    cached = get_cached_json(cache_key)
    if cached is not None:
        return cached

    payload = _request_amap("/geocode/geo", {"address": address, "city": city or AMAP_DEFAULT_CITY})
    geocodes = payload.get("geocodes", [])
    if not geocodes:
        return None
    first = geocodes[0]
    lat, lng = _split_location(first.get("location"))
    result = {
        "formatted_address": first.get("formatted_address", address),
        "province": first.get("province"), "city": first.get("city"),
        "district": first.get("district"), "adcode": first.get("adcode"),
        "latitude": lat, "longitude": lng,
    }
    set_cached_json(cache_key, result, expire_seconds=REDIS_MAP_TTL_SECONDS)
    return result


def search_places(keyword: str, city: str | None = None, page_size: int = 5) -> list[dict[str, Any]]:
    """根据关键词搜索 POI。"""
    cache_key = f"map:place:{_normalize_cache_text(keyword)}:{_normalize_cache_text(city or AMAP_DEFAULT_CITY)}:{page_size}"
    cached = get_cached_json(cache_key)
    if cached is not None:
        return cached

    payload = _request_amap("/place/text", {
        "keywords": keyword, "city": city or AMAP_DEFAULT_CITY,
        "offset": page_size, "page": 1, "extensions": "all",
    })
    pois = payload.get("pois", [])
    results: list[dict[str, Any]] = []
    for poi in pois:
        lat, lng = _split_location(poi.get("location"))
        photos = poi.get("photos") if isinstance(poi.get("photos"), list) else []
        first_photo = photos[0] if photos and isinstance(photos[0], dict) else {}
        results.append({
            "name": poi.get("name"), "address": poi.get("address"),
            "cityname": poi.get("cityname"), "adname": poi.get("adname"),
            "type": poi.get("type"), "poi_id": poi.get("id"),
            "image_url": first_photo.get("url"),
            "latitude": lat, "longitude": lng,
        })
    set_cached_json(cache_key, results, expire_seconds=REDIS_MAP_TTL_SECONDS)
    return results


def estimate_route(
    origin_lng: float, origin_lat: float,
    dest_lng: float, dest_lat: float,
) -> dict[str, Any] | None:
    """估算两点之间的驾车距离和耗时。"""
    cache_key = f"map:route:{origin_lng:.6f},{origin_lat:.6f}:{dest_lng:.6f},{dest_lat:.6f}"
    cached = get_cached_json(cache_key)
    if cached is not None:
        return cached

    payload = _request_amap("/direction/driving", {
        "origin": f"{origin_lng},{origin_lat}",
        "destination": f"{dest_lng},{dest_lat}",
        "strategy": 0,
    })
    route = payload.get("route", {})
    paths = route.get("paths", [])
    if not paths:
        return None
    first = paths[0]
    dist = _parse_float(first.get("distance"))
    dur = _parse_float(first.get("duration"))
    result = {
        "distance_meters": dist,
        "distance_km": round(dist / 1000, 2) if dist is not None else None,
        "duration_seconds": dur,
        "estimated_minutes": round(dur / 60) if dur is not None else None,
        "taxi_cost": _parse_float(route.get("taxi_cost")),
    }
    set_cached_json(cache_key, result, expire_seconds=REDIS_MAP_TTL_SECONDS)
    return result


# ─── 供 routes 使用的简化接口 ─────────────────────────────

def search_poi(keyword: str, city: str) -> dict[str, Any]:
    """[兼容旧接口] POI 搜索。"""
    places = search_places(keyword=keyword, city=city)
    return {"keyword": keyword, "city": city, "pois": places}


def get_route(origin: str, destination: str) -> dict[str, Any]:
    """[兼容旧接口] 路径规划。"""
    origin_parts = origin.split(",")
    dest_parts = destination.split(",")
    o_lng, o_lat = float(origin_parts[0]), float(origin_parts[1])
    d_lng, d_lat = float(dest_parts[0]), float(dest_parts[1])
    result = estimate_route(o_lng, o_lat, d_lng, d_lat)
    return {"origin": origin, "destination": destination, "route": result}


def enrich_itinerary_with_map_data(itinerary: Itinerary, city: str | None = None) -> Itinerary:
    """使用高德服务补全 itinerary 里的地址、坐标等信息。"""
    enriched_count = 0
    dest = city or itinerary.destination
    for day in itinerary.days:
        for spot in day.spots:
            try:
                places = search_places(spot.name, city=dest, page_size=1)
                if places:
                    p = places[0]
                    spot.address = p.get("address") or spot.address
                    spot.latitude = p.get("latitude")
                    spot.longitude = p.get("longitude")
                    spot.poi_id = p.get("poi_id") or spot.poi_id
                    spot.image_url = p.get("image_url") or spot.image_url
                    enriched_count += 1
            except Exception:
                continue
        if day.hotel is not None:
            try:
                places = search_places(day.hotel.name, city=dest, page_size=1)
                if places:
                    p = places[0]
                    day.hotel.address = p.get("address") or day.hotel.address
                    day.hotel.latitude = p.get("latitude")
                    day.hotel.longitude = p.get("longitude")
                    enriched_count += 1
            except Exception:
                pass
    if enriched_count > 0:
        note = "已补充高德地图地址、坐标信息。"
        if note not in itinerary.source_notes:
            itinerary.source_notes.append(note)
    return itinerary
