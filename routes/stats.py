from fastapi import APIRouter
from database import get_db, get_cursor

router = APIRouter()

@router.get("/api/stats")
async def get_stats():
    """Get dashboard statistics"""
    conn = get_db()
    cursor = get_cursor(conn)
    
    try:
        # Get total patients
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_patients = cursor.fetchone()['count']
        
        # Get active alarms count
        cursor.execute("SELECT COUNT(*) as count FROM alarms WHERE status = 'active'")
        active_alarms = cursor.fetchone()['count']
        
        # Get distance violations (active alarms of type distance_violation)
        cursor.execute("""
            SELECT COUNT(*) as count FROM alarms 
            WHERE status = 'active' AND alarm_type = 'distance_violation'
        """)
        distance_violations = cursor.fetchone()['count']
        
        # Get restricted area violations (active alarms of type restricted_area)
        cursor.execute("""
            SELECT COUNT(*) as count FROM alarms 
            WHERE status = 'active' AND alarm_type = 'restricted_area'
        """)
        restricted_areas = cursor.fetchone()['count']
        
        # Get no update violations (active alarms of type no_update)
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