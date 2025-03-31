import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db, get_cursor

def create_test_no_update_alarms():
    """Create 5 test no_update alarms for random existing users"""
    try:
        conn = get_db()
        cursor = get_cursor(conn)

        # Get 5 random users that have location records
        cursor.execute("""
            SELECT DISTINCT u.id, u.username 
            FROM users u
            JOIN locations l ON u.id = l.user_id
            ORDER BY RAND()
            LIMIT 5
        """)
        users = cursor.fetchall()

        # Create no_update alarms for these users
        for user in users:
            cursor.execute("""
                INSERT INTO alarms 
                (user_id, alarm_type, timestamp, status, distance) 
                VALUES (%s, 'no_update', NOW(), 'active', NULL)
            """, (user['id'],))
            print(f"Created no_update alarm for user {user['username']} (ID: {user['id']})")

        conn.commit()
        print("\nSuccessfully created 5 test no_update alarms")

    except Exception as e:
        print(f"Error creating test alarms: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_test_no_update_alarms() 