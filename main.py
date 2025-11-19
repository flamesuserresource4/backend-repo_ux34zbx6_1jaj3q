import os
from datetime import date
from bson import ObjectId
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from database import db, create_document, get_documents
from schemas import Car, Booking

app = FastAPI(title="Car Rental API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Car Rental API is running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# --------- Car Endpoints ---------

class CarOut(Car):
    id: str

@app.get("/api/cars", response_model=List[CarOut])
def list_cars():
    docs = get_documents("car")
    cars: List[CarOut] = []
    for d in docs:
        car = {k: v for k, v in d.items() if k != "_id"}
        car["id"] = str(d.get("_id"))
        cars.append(car)  # type: ignore
    return cars

@app.post("/api/cars", status_code=201)
def add_car(car: Car):
    inserted_id = create_document("car", car)
    return {"id": inserted_id}

# --------- Booking Endpoints ---------

class BookingResponse(BaseModel):
    id: str

@app.get("/api/bookings")
def list_bookings():
    docs = get_documents("booking")
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs

@app.post("/api/bookings", response_model=BookingResponse, status_code=201)
def create_booking(payload: Booking):
    # Validate that end_date is within 30 days from start_date
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="End date cannot be before start date")
    delta = (payload.end_date - payload.start_date).days + 1
    if delta > 31:
        raise HTTPException(status_code=400, detail="Max rental length is 30 days")

    # Ensure the car exists
    car = db["car"].find_one({"_id": ObjectId(payload.car_id)}) if ObjectId.is_valid(payload.car_id) else None
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    # Check overlap with existing bookings for the same car
    new_start = payload.start_date.isoformat()
    new_end = payload.end_date.isoformat()
    overlap = db["booking"].find_one({
        "car_id": payload.car_id,
        "$and": [
            {"start_date": {"$lte": new_end}},
            {"end_date": {"$gte": new_start}},
        ],
    })
    if overlap:
        raise HTTPException(status_code=409, detail="Selected dates overlap with an existing booking for this car")

    # Insert
    data = payload.model_dump()
    data["start_date"] = new_start
    data["end_date"] = new_end
    inserted_id = create_document("booking", data)
    return {"id": inserted_id}

# Utility endpoint to seed some cars (for demo)
@app.post("/api/seed")
def seed_cars():
    if db["car"].count_documents({}) > 0:
        return {"status": "already-seeded"}
    sample = [
        {"make": "Skoda", "model": "Octavia", "year": 2020, "transmission": "Automatic", "seats": 5, "fuel": "Petrol", "price_per_day": 39.0, "image": "https://images.unsplash.com/photo-1549921296-3b4a8417b9a5"},
        {"make": "Volkswagen", "model": "Golf", "year": 2019, "transmission": "Manual", "seats": 5, "fuel": "Diesel", "price_per_day": 35.0, "image": "https://images.unsplash.com/photo-1619767886558-efdc259cde1e"},
        {"make": "Toyota", "model": "Corolla", "year": 2021, "transmission": "Automatic", "seats": 5, "fuel": "Hybrid", "price_per_day": 42.0, "image": "https://images.unsplash.com/photo-1493236296276-d17357e28809"},
        {"make": "Hyundai", "model": "i30", "year": 2018, "transmission": "Manual", "seats": 5, "fuel": "Petrol", "price_per_day": 29.0, "image": "https://images.unsplash.com/photo-1552519507-da3b142c6e3d"},
        {"make": "Tesla", "model": "Model 3", "year": 2022, "transmission": "Automatic", "seats": 5, "fuel": "EV", "price_per_day": 79.0, "image": "https://images.unsplash.com/photo-1552519507-88aaecf2485b"},
    ]
    for s in sample:
        create_document("car", s)
    return {"status": "seeded", "count": len(sample)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
