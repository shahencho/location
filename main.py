from fastapi import FastAPI, Request
from routes import locations
from fastapi.middleware.cors import CORSMiddleware
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

app = FastAPI(title="OwnTracks Location API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include location routes
app.include_router(locations.router)

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

@app.get("/")
def health_check():
    return {"status": "running", "time": datetime.datetime.now().isoformat()}
