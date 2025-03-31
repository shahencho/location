from fastapi import APIRouter
from database import get_db, get_cursor
from datetime import datetime, timedelta
import math
from config import MONITORING_CONFIG, MAP_CONFIG

router = APIRouter()

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers"""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance * 1000  # Convert to meters for easier comparison

@router.post("/api/generate-alarms")
async def generate_alarms():
    """Generate alarms based on current violations"""
    conn = get_db()
    cursor = get_cursor(conn)
    
    try:
        # Get all users with their latest locations and home locations
        cursor.execute("""
            SELECT 
                u.id,
                u.username,
                u.home_lat,
                u.home_lng,
                u.home_location_set,
                l.lat,
                l.lng,
                l.timestamp as last_update
            FROM users u
            LEFT JOIN (
                SELECT l1.*
                FROM locations l1
                INNER JOIN (
                    SELECT user_id, MAX(timestamp) as max_timestamp
                    FROM locations
                    GROUP BY user_id
                ) l2 ON l1.user_id = l2.user_id AND l1.timestamp = l2.max_timestamp
            ) l ON u.id = l.user_id
            WHERE u.home_location_set = 1
        """)
        
        users = cursor.fetchall()
        now = datetime.now()
        alarms_created = 0
        
        for user in users:
            # Skip if no location data
            if not user['lat'] or not user['lng']:
                continue
                
            # 1. Check distance violations (if more than allowed radius from home)
            distance = calculate_distance(
                user['home_lat'], user['home_lng'],
                user['lat'], user['lng']
            )
            
            if distance > MONITORING_CONFIG["ALLOWED_RADIUS"]:
                cursor.execute("""
                    INSERT INTO alarms (user_id, alarm_type, distance, timestamp, status)
                    VALUES (%s, 'distance_violation', %s, NOW(), 'active')
                    ON DUPLICATE KEY UPDATE 
                    timestamp = IF(status = 'resolved', NOW(), timestamp),
                    status = IF(status = 'resolved', 'active', status),
                    distance = %s
                """, (user['id'], distance, distance))
                alarms_created += cursor.rowcount
            
            # 2. Check for restricted area violations
            cursor.execute("""
                SELECT id, name 
                FROM hospitals h
                WHERE ST_Contains(
                    ST_Buffer(Point(h.latitude, h.longitude), %s),
                    Point(%s, %s)
                )
            """, (MAP_CONFIG["RESTRICTED_ZONE_OFFSET"], user['lat'], user['lng']))
            
            if cursor.fetchone():
                cursor.execute("""
                    INSERT INTO alarms (user_id, alarm_type, timestamp, status)
                    VALUES (%s, 'restricted_area', NOW(), 'active')
                    ON DUPLICATE KEY UPDATE 
                    timestamp = IF(status = 'resolved', NOW(), timestamp),
                    status = IF(status = 'resolved', 'active', status)
                """, (user['id'],))
                alarms_created += cursor.rowcount
            
            # 3. Check for no updates (if last update is more than NO_UPDATE_THRESHOLD old)
            if user['last_update'] and (now - user['last_update']).total_seconds() > MONITORING_CONFIG["NO_UPDATE_THRESHOLD"]:
                cursor.execute("""
                    INSERT INTO alarms (user_id, alarm_type, timestamp, status)
                    VALUES (%s, 'no_update', NOW(), 'active')
                    ON DUPLICATE KEY UPDATE 
                    timestamp = IF(status = 'resolved', NOW(), timestamp),
                    status = IF(status = 'resolved', 'active', status)
                """, (user['id'],))
                alarms_created += cursor.rowcount
        
        conn.commit()
        return {"status": "success", "alarms_created": alarms_created}
        
    finally:
        cursor.close()
        conn.close()

# Add a unique constraint to prevent duplicate active alarms
def setup_alarm_constraints():
    conn = get_db()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            ALTER TABLE alarms 
            ADD UNIQUE INDEX idx_unique_active_alarm (user_id, alarm_type, status),
            ADD INDEX idx_alarm_status (status)
        """)
        conn.commit()
    except Exception as e:
        print(f"Warning: Could not create index - it might already exist: {e}")
    finally:
        cursor.close()
        conn.close() 