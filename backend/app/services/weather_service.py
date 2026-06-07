"""天气服务 —— 调用高德天气 API + 缓存。"""
from __future__ import annotations
import logging
from typing import Any
import httpx
from app.config import (
    AMAP_API_KEY, AMAP_BASE_URL, AMAP_TIMEOUT_SECONDS, REDIS_WEATHER_TTL_SECONDS,
)
from app.services.cache_service import get_cached_json, set_cached_json
from app.services.map_service import geocode_address

logger = logging.getLogger(__name__)


def _ensure_key() -> None:
    if not AMAP_API_KEY:
        raise RuntimeError("当前环境未配置 AMAP_API_KEY，无法调用天气服务。")


def _request_amap_weather(path: str, params: dict[str, Any]) -> dict[str, Any]:
    _ensure_key()
    with httpx.Client(timeout=AMAP_TIMEOUT_SECONDS) as client:
        resp = client.get(f"{AMAP_BASE_URL}{path}", params={"key": AMAP_API_KEY, **params})
        resp.raise_for_status()
        payload = resp.json()
    if payload.get("status") != "1":
        raise RuntimeError(f"高德天气接口调用失败：{payload.get('info', '未知错误')}")
    return payload


def _normalize_cache_text(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip().lower()


def get_weather_forecast(city: str) -> dict[str, Any]:
    """获取指定城市的未来天气预报。"""
    cache_key = f"weather:forecast:{_normalize_cache_text(city)}"
    cached = get_cached_json(cache_key)
    if cached is not None:
        logger.info("weather cache hit: city=%s", city)
        return cached
    logger.info("weather cache miss: city=%s", city)

    geocode = geocode_address(city, city=city)
    city_code = geocode.get("adcode") if geocode else city

    payload = _request_amap_weather(
        "/weather/weatherInfo",
        {"city": city_code or city, "extensions": "all"},
    )
    forecasts = payload.get("forecasts", [])
    if not forecasts:
        raise RuntimeError("未获取到天气预报结果。")

    first = forecasts[0]
    casts = first.get("casts", [])
    days = [
        {
            "date": c.get("date"), "week": c.get("week"),
            "day_weather": c.get("dayweather"), "night_weather": c.get("nightweather"),
            "day_temp": c.get("daytemp"), "night_temp": c.get("nighttemp"),
            "day_wind": c.get("daywind"), "night_wind": c.get("nightwind"),
        }
        for c in casts
    ]
    result = {
        "city": first.get("city") or city,
        "province": first.get("province"),
        "adcode": first.get("adcode"),
        "report_time": first.get("reporttime"),
        "days": days,
    }
    set_cached_json(cache_key, result, expire_seconds=REDIS_WEATHER_TTL_SECONDS)
    return result
