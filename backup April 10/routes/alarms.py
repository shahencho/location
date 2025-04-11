from fastapi import APIRouter, HTTPException
from database import get_db, get_cursor
from datetime import datetime

router = APIRouter()

@router.get("/api/alarms")
async def get_alarms():
    """Get all active alarms"""
    try:
        conn = get_db()
        cursor = get_cursor(conn)
        
        # Get all active alarms with user details
        cursor.execute("""
            SELECT 
                a.id,
                a.user_id as patient_id,
                a.alarm_type,
                a.distance,
                a.timestamp,
                a.status,
                u.username as patient_name
            FROM alarms a
            JOIN users u ON a.user_id = u.id
            WHERE a.status = 'active'
            ORDER BY a.timestamp DESC
        """)
        
        alarms = []
        for row in cursor.fetchall():
            # Format the alarm message based on type
            message = ""
            if row['alarm_type'] == 'distance_violation':
                distance = round(row['distance'], 1)
                message = f"{row['patient_name']} is {distance}m outside their allowed radius"
            elif row['alarm_type'] == 'restricted_area':
                message = f"{row['patient_name']} has entered a restricted area"
            elif row['alarm_type'] == 'no_update':
                message = f"No location updates received from {row['patient_name']}"
            
            alarms.append({
                'id': row['id'],
                'patient_id': row['patient_id'],
                'type': row['alarm_type'],
                'message': message,
                'timestamp': row['timestamp'].isoformat(),
                'patient_name': row['patient_name']
            })
        
        cursor.close()
        conn.close()
        
        return alarms
    except Exception as e:
        print(f"Error getting alarms: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/alarms/{alarm_id}/resolve")
async def resolve_alarm(alarm_id: int):
    """Resolve an alarm"""
    conn = get_db()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            UPDATE alarms 
            SET status = 'resolved', 
                resolved_at = NOW() 
            WHERE id = %s AND status = 'active'
        """, (alarm_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Alarm not found or already resolved")
            
        conn.commit()
        return {"status": "success", "message": "Alarm resolved successfully"}
        
    finally:
        cursor.close()
        conn.close() 