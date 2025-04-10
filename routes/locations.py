from fastapi import APIRouter
import traceback
from database import get_db  # Adjust if your DB helper is elsewhere

router = APIRouter()

@router.get("/last-location")
def get_last_location(tid: str = None):
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        if tid:
            cursor.execute("""
                SELECT *
                FROM locations
                WHERE tid = %s
                ORDER BY timestamp DESC
                LIMIT 1
            """, (tid,))
        else:
            cursor.execute("""
                SELECT l.*
                FROM locations l
                INNER JOIN (
                    SELECT tid, MAX(id) as max_id
                    FROM locations
                    GROUP BY tid
                ) latest ON l.id = latest.max_id
                ORDER BY l.timestamp DESC
            """)

        rows = cursor.fetchall()
        return {"status": "ok", "data": rows}

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
