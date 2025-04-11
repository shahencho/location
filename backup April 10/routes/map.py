from fastapi import APIRouter, HTTPException
from database import get_db, get_cursor
from config import MAP_CONFIG

router = APIRouter()

@router.get("/api/map-data")
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
            offset = MAP_CONFIG["RESTRICTED_ZONE_OFFSET"]
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
                "radius": MAP_CONFIG["DEFAULT_ALLOWED_RADIUS"]
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