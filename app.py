from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from database import get_db, get_cursor

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/stats")
async def get_stats():
    conn = get_db()
    cursor = get_cursor(conn)
    
    try:
        # Get total patients
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_patients = cursor.fetchone()['count']
        
        # Get active alarms count
        cursor.execute("SELECT COUNT(*) as count FROM alarms WHERE status = 'active'")
        active_alarms = cursor.fetchone()['count']
        
        # Get distance violations
        cursor.execute("""
            SELECT COUNT(*) as count FROM alarms 
            WHERE status = 'active' AND alarm_type = 'distance_violation'
        """)
        distance_violations = cursor.fetchone()['count']
        
        # Get restricted area violations
        cursor.execute("""
            SELECT COUNT(*) as count FROM alarms 
            WHERE status = 'active' AND alarm_type = 'restricted_area'
        """)
        restricted_areas = cursor.fetchone()['count']
        
        # Get no update violations
        cursor.execute("""
            SELECT COUNT(*) as count FROM alarms 
            WHERE status = 'active' AND alarm_type = 'no_update'
        """)
        no_updates = cursor.fetchone()['count']
        
        return {
            "total_patients": total_patients,
            "active_alarms": active_alarms,
            "distance_violations": distance_violations,
            "restricted_areas": restricted_areas,
            "no_updates": no_updates
        }
    finally:
        cursor.close()
        conn.close()

@app.get("/api/map-data")
async def get_map_data():
    conn = get_db()
    cursor = get_cursor(conn)
    
    try:
        # Get all patients with their latest locations
        cursor.execute("""
            SELECT 
                u.id,
                u.username as name,
                l.lat,
                l.lng,
                l.timestamp as last_update,
                COALESCE(a.alarm_type, 'none') as violation_type,
                a.status
            FROM users u
            LEFT JOIN (
                SELECT user_id, lat, lng, timestamp
                FROM locations l1
                WHERE timestamp = (
                    SELECT MAX(timestamp)
                    FROM locations l2
                    WHERE l2.user_id = l1.user_id
                )
            ) l ON u.id = l.user_id
            LEFT JOIN alarms a ON u.id = a.user_id AND a.status = 'active'
        """)
        patients = cursor.fetchall()

        # Get all hospitals (restricted zones)
        cursor.execute("""
            SELECT 
                id,
                name,
                latitude,
                longitude
            FROM hospitals
        """)
        hospitals = cursor.fetchall()

        # Convert hospitals to restricted zones format
        restricted_zones = []
        for hospital in hospitals:
            # Create a square zone around each hospital
            lat = hospital['latitude']
            lng = hospital['longitude']
            offset = 0.001  # Roughly 100 meters
            restricted_zones.append({
                "id": hospital['id'],
                "name": hospital['name'],
                "coordinates": [
                    {"lat": lat - offset, "lng": lng - offset},
                    {"lat": lat + offset, "lng": lng - offset},
                    {"lat": lat + offset, "lng": lng + offset},
                    {"lat": lat - offset, "lng": lng + offset}
                ]
            })

        # Get all users' home locations for allowed radiuses
        cursor.execute("""
            SELECT 
                id,
                username as name,
                home_lat as lat,
                home_lng as lng
            FROM users
            WHERE home_location_set = 1
        """)
        allowed_radiuses = []
        for user in cursor.fetchall():
            allowed_radiuses.append({
                "id": user['id'],
                "name": f"Allowed area for {user['name']}",
                "lat": user['lat'],
                "lng": user['lng'],
                "radius": 500000   # 500 kilometers radius (500,000 meters)
            })

        return {
            "patients": patients,
            "restricted_zones": restricted_zones,
            "allowed_radiuses": allowed_radiuses
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 