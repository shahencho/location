from fastapi import APIRouter, HTTPException
from database import get_db, get_cursor
from datetime import datetime

router = APIRouter()

@router.get("/api/stats")
async def get_stats():
    """Get dashboard statistics"""
    try:
        conn = get_db()
        cursor = get_cursor(conn)

        # Get total number of active alarms
        cursor.execute("""
            SELECT COUNT(*) as count FROM alarms 
            WHERE status = 'active'
        """)
        active_alarms = cursor.fetchone()['count']

        # Get total number of patients
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_patients = cursor.fetchone()['count']

        # Get number of active distance violations
        cursor.execute("""
            SELECT COUNT(*) as count FROM alarms 
            WHERE alarm_type = 'distance_violation' 
            AND status = 'active'
        """)
        distance_violations = cursor.fetchone()['count']

        # Get number of active restricted area violations
        cursor.execute("""
            SELECT COUNT(*) as count FROM alarms 
            WHERE alarm_type = 'restricted_area' 
            AND status = 'active'
        """)
        restricted_areas = cursor.fetchone()['count']

        # Get number of patients with no recent updates (more than 10 minutes)
        cursor.execute("""
            SELECT COUNT(*) as count FROM users u
            LEFT JOIN locations l ON u.id = l.user_id
            WHERE l.id IS NULL OR 
            TIMESTAMPDIFF(MINUTE, l.timestamp, NOW()) > 10
        """)
        no_updates = cursor.fetchone()['count']

        cursor.close()
        conn.close()

        return {
            "active_alarms": active_alarms,
            "total_patients": total_patients,
            "distance_violations": distance_violations,
            "restricted_areas": restricted_areas,
            "no_updates": no_updates
        }
    except Exception as e:
        print(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 