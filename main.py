from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routes import locations, stats, map, config, alarms, alarm_generator
import os
import datetime
import json
from database import get_db
from pydantic import BaseModel, Field
from typing import Literal

class LocationUpdate(BaseModel):
    type: Literal["location"] = Field(..., description="Must be 'location'", alias="_type")
    lat: float = Field(..., description="Latitude", example=34.0522)
    lon: float = Field(..., description="Longitude", example=-118.2437)
    tst: int = Field(..., description="Timestamp in Unix format", example=1677686400)
    tid: str = Field(..., description="Device/Tracker ID", example="device1")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

app = FastAPI(title="Location Monitoring Dashboard")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount templates directory
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(locations.router)
app.include_router(stats.router)
app.include_router(map.router)
app.include_router(config.router)
app.include_router(alarms.router)
app.include_router(alarm_generator.router)

@app.get("/")
async def home(request: Request):
    """Serve the dashboard HTML"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/location", summary="Update device location")
async def receive_location(location: LocationUpdate):
    print(f"?? [{datetime.datetime.now()}] Received from device: {location.model_dump()}")

    timestamp = datetime.datetime.fromtimestamp(location.tst)

    conn = None
    cursor = None

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (location.tid,))
        result = cursor.fetchone()

        if result:
            user_id = result['id']
        else:
            # Register new user with initial location
            cursor.execute(
                "INSERT INTO users (username, initial_lat, initial_lng) VALUES (%s, %s, %s)",
                (location.tid, location.lat, location.lon)
            )
            conn.commit()
            user_id = cursor.lastrowid

        # Insert location record
        cursor.execute(
            "INSERT INTO locations (user_id, tid, lat, lng, timestamp, source_payload) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, location.tid, location.lat, location.lon, timestamp, json.dumps(location.model_dump()))
        )
        conn.commit()

        return {
            "status": "ok",
            "user_id": user_id,
            "username": location.tid,
            "location": {
                "lat": location.lat,
                "lon": location.lon
            },
            "timestamp": timestamp.isoformat()
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
