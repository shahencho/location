from database import get_db

def check_database():
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check users table
        cursor.execute("DESCRIBE users")
        print("\nUsers table structure:")
        for column in cursor.fetchall():
            print(column)
            
        # Check alarms table
        cursor.execute("DESCRIBE alarms")
        print("\nAlarms table structure:")
        for column in cursor.fetchall():
            print(column)
            
        # Check if we have any data
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"\nNumber of users: {user_count}")
        
        cursor.execute("SELECT COUNT(*) FROM alarms")
        alarm_count = cursor.fetchone()[0]
        print(f"Number of alarms: {alarm_count}")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_database() 