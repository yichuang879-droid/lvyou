from fastapi import FastAPI, HTTPException
from app.schemas import TripGenerateRequest, TripPlan
from app.services.trip_service import generate_trip
from app.storage.memory_store import get_trip, list_trips, delete_trip

app = FastAPI(title="旅游规划助手 Backend MVP")


@app.get("/health")
def health():
    return {"status": "所有检查都ok"}


@app.post("/trip/generate", response_model=TripPlan)
def create_trip(req: TripGenerateRequest):
    return generate_trip(req)


@app.get("/trip/history")
def history():
    return list_trips()


@app.get("/trip/{trip_id}", response_model=TripPlan)
def detail(trip_id: str):
    trip = get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@app.delete("/trip/{trip_id}")
def remove(trip_id: str):
    ok = delete_trip(trip_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Trip not found")
    return {"deleted": True}