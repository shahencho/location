# Map Configuration
MAP_CONFIG = {
    # Default center coordinates for Los Angeles
    "LA_CENTER": {
        "lat": 34.0522,
        "lng": -118.2437
    },
    
    # LA County bounds
    "LA_BOUNDS": {
        "north": 34.3373,  # North LA county
        "south": 33.7037,  # South LA county
        "west": -118.6682, # West LA county
        "east": -117.8067  # East LA county
    },
    
    # Default zoom levels
    "DEFAULT_ZOOM": 8,
    "RESET_ZOOM": 8,
    
    # Radius settings (in meters)
    "DEFAULT_ALLOWED_RADIUS": 10000,  # 10km default radius
    
    # Colors
    "MARKER_COLOR": "#FF0000",        # Red for patient markers
    "RESTRICTED_ZONE_COLOR": "#FF4500", # OrangeRed for restricted zones
    "ALLOWED_RADIUS_COLOR": "#32CD32",  # LimeGreen for allowed radius
    
    # Zone settings
    "RESTRICTED_ZONE_OFFSET": 0.001,  # ~100 meters square around hospitals
    
    # Styling
    "MARKER_SCALE": 12,
    "STROKE_WEIGHT": 3,
    "FILL_OPACITY": 0.2,
    "STROKE_OPACITY": 0.8
}

# Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "database": "location_monitoring",
    # Other DB settings should be loaded from environment variables
}

# Monitoring Configuration
MONITORING_CONFIG = {
    "UPDATE_INTERVAL": 600000,  # 10 minutes in milliseconds (frontend refresh rate)
    "EXPECTED_UPDATE_INTERVAL": 10800,  # 3 hours in seconds (expected location update frequency)
    "NO_UPDATE_THRESHOLD": 32400,  # 9 hours in seconds (trigger alarm if no update)
    "RESTRICTED_ZONE_RADIUS": 100,  # meters (matches RESTRICTED_ZONE_OFFSET)
    "ALLOWED_RADIUS": MAP_CONFIG["DEFAULT_ALLOWED_RADIUS"]  # Use the same value as map config
} 