from fastapi import FastAPI, Request, HTTPException
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
import time

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

# Rate limiting: Store last update time for each device
last_updates = {}
MINIMUM_UPDATE_INTERVAL = 1200  # 20 minutes in seconds
LOG_INTERVAL = 3600  # 1 hour in seconds

async def initialize_last_updates():
    """Initialize last_updates dictionary with data from DB"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get the most recent update for each tid
        cursor.execute("""
            SELECT tid, MAX(timestamp) as last_update
            FROM locations
            GROUP BY tid
        """)
        
        print("\nInitializing rate limiting with last update times:")
        print("-" * 60)
        print(f"{'Device ID':<20} {'Last Update Time':<30}")
        print("-" * 60)
        
        for row in cursor.fetchall():
            # Convert timestamp to unix time for consistency
            last_updates[row['tid']] = row['last_update'].timestamp()
            # Format timestamp for logging
            formatted_time = row['last_update'].strftime('%Y-%m-%d %H:%M:%S')
            print(f"{row['tid']:<20} {formatted_time:<30}")
            
        print("-" * 60)
        print(f"Total devices initialized: {len(last_updates)}\n")
            
    except Exception as e:
        print(f"Warning: Could not initialize last_updates: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.on_event("startup")
async def startup_event():
    await initialize_last_updates()

class LocationUpdate(BaseModel):
    type: Literal["location"] = Field(..., description="Must be 'location'", alias="_type")
    lat: float = Field(..., description="Latitude", example=34.0522)
    lon: float = Field(..., description="Longitude", example=-118.2437)
    tst: int = Field(..., description="Timestamp in Unix format", example=1677686400)
    tid: str = Field(..., description="Device/Tracker ID", example="device1")

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

@app.get("/")
async def home(request: Request):
    """Serve the dashboard HTML"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/location", summary="Update device location")
async def receive_location(location: LocationUpdate):
    tid = location.tid
    incoming_time = location.tst  # Unix timestamp from the request

    # Check if we have a recent update for this tid
    if tid in last_updates:
        last_update_time = last_updates[tid]
        time_since_last_update = incoming_time - last_update_time
        
        # If update is too frequent (less than 20 minutes), ignore it completely
        if time_since_last_update < MINIMUM_UPDATE_INTERVAL:
            # Log once per hour using integer division
            if int(incoming_time/LOG_INTERVAL) > int(last_update_time/LOG_INTERVAL):
                print(f"Warning: Frequent updates from {tid}. Last update was {time_since_last_update:.0f} seconds ago")
            # Return early - don't do any database operations
            return {
                "status": "ok",
                "message": "Update ignored due to rate limiting"
            }

    # If we get here, enough time has passed - process the update
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # Create timestamp at the beginning
        timestamp = datetime.datetime.fromtimestamp(location.tst)

        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (location.tid,))
        result = cursor.fetchone()

        if result:
            user_id = result['id']
            # Update last_seen
            cursor.execute(
                "UPDATE users SET last_seen = %s WHERE id = %s",
                (timestamp, user_id)
            )
        else:
            # Register new user with initial location
            cursor.execute(
                "INSERT INTO users (username, initial_lat, initial_lng, last_seen) VALUES (%s, %s, %s, %s)",
                (location.tid, location.lat, location.lon, timestamp)
            )
            conn.commit()
            user_id = cursor.lastrowid

        # Insert location record
        cursor.execute(
            "INSERT INTO locations (user_id, tid, lat, lng, timestamp, source_payload) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, location.tid, location.lat, location.lon, timestamp, json.dumps(location.model_dump()))
        )
        conn.commit()

        # Update last_updates only after successful database operation
        last_updates[tid] = incoming_time

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
