import os
import mysql.connector
from dotenv import load_dotenv
import math

# Load .env values into environment
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def get_cursor(conn):
    """Get a cursor that returns results as dictionaries"""
    return conn.cursor(dictionary=True, buffered=True)

def init_db():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Drop violations table if it exists (due to foreign key constraints)
        cursor.execute("DROP TABLE IF EXISTS violations")

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                initial_lat REAL,
                initial_lng REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                home_lat REAL,
                home_lng REAL,
                home_location_set BOOLEAN DEFAULT 0
            )
        """)

        # Create locations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tid TEXT NOT NULL,
                lat REAL NOT NULL,
                lng REAL NOT NULL,
                timestamp DATETIME NOT NULL,
                source_payload TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create alarms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alarms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                alarm_type TEXT NOT NULL CHECK(alarm_type IN ('distance_violation', 'restricted_area', 'no_update')),
                distance REAL,
                timestamp DATETIME NOT NULL,
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'resolved')),
                resolution_comment TEXT,
                resolved_at TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create hospitals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hospitals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert sample hospitals data
        hospitals_data = [
            ("Providence Saint Joseph Medical Center", 34.1489, -118.3337),
            ("Glendale Memorial Hospital", 34.1425, -118.2551),
            ("USC Verdugo Hills Hospital", 34.2279, -118.2359),
            ("Adventist Health Glendale", 34.1506, -118.2442),
            ("Hollywood Presbyterian Medical Center", 34.0904, -118.2956)
        ]

        # Clear existing data
        cursor.executemany(
            "INSERT INTO hospitals (name, latitude, longitude) VALUES (?, ?, ?)",
            hospitals_data
        )

        # Create violations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                hospital_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved BOOLEAN DEFAULT 0,
                resolution_comment TEXT DEFAULT NULL,
                resolved_at TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
            )
        """)

        conn.commit()
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points using the Haversine formula
    Returns distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def test_db_connection():
    """Test database connection and table structure"""
    try:
        conn = get_db()
        cursor = get_cursor(conn)
        
        # Test connection by getting tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("Connected to database successfully!")
        print("Available tables:", [table['Tables_in_' + DB_CONFIG['database']] for table in tables])
        
        # Test each table structure
        for table in ['users', 'locations', 'alarms', 'hospitals', 'violations']:
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            print(f"\n{table} table structure:")
            for column in columns:
                print(f"- {column['Field']}: {column['Type']}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error testing database connection: {str(e)}")
        return False

if __name__ == "__main__":
    test_db_connection()
