🔧 Step-by-Step Implementation
Step 1: Ensure required schema is in place
You must have these tables:

sql
Copy
Edit
-- alarm_config (key-value store)
CREATE TABLE alarm_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value FLOAT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- alarms (to store triggered alarms)
CREATE TABLE alarms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    alarm_type VARCHAR(50) NOT NULL,
    distance FLOAT NULL,
    timestamp DATETIME NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    resolved_at DATETIME DEFAULT NULL
);

-- locations (must include user_id and timestamp fields)
-- users (used to verify user_id and optionally set home_lat/lng)
Step 2: Insert a configuration value
sql
Copy
Edit
INSERT INTO alarm_config (config_key, config_value)
VALUES ('alarm_hours', 3)
ON DUPLICATE KEY UPDATE config_value = VALUES(config_value);
You can change 3 to 9 or any desired number of hours.

Step 3: Create the stored procedure
sql
Copy
Edit
DROP PROCEDURE IF EXISTS check_inactive_users;

DELIMITER //

CREATE PROCEDURE check_inactive_users()
BEGIN
    DECLARE alarm_hours_config INT;

    -- Fetch the configured inactivity window (e.g. 3 or 9 hours)
    SELECT config_value INTO alarm_hours_config
    FROM alarm_config
    WHERE config_key = 'alarm_hours'
    LIMIT 1;

    -- Insert alarms for users inactive longer than threshold
    INSERT INTO alarms (user_id, alarm_type, timestamp, status)
    SELECT 
        l.user_id,
        'no_update',
        NOW(),
        'active'
    FROM (
        SELECT user_id, MAX(timestamp) AS last_update_time
        FROM locations
        GROUP BY user_id
    ) l
    WHERE l.last_update_time < NOW() - INTERVAL alarm_hours_config HOUR
    AND NOT EXISTS (
        SELECT 1 FROM alarms a
        WHERE a.user_id = l.user_id
          AND a.alarm_type = 'no_update'
          AND a.status = 'active'
    );
END;
//

DELIMITER ;
Step 4: Test manually
sql
Copy
Edit
CALL check_inactive_users();

SELECT * FROM alarms WHERE alarm_type = 'no_update';
Step 5: Create a scheduled event to run it every hour
sql
Copy
Edit
DELIMITER //

CREATE EVENT IF NOT EXISTS check_inactive_users_event
ON SCHEDULE EVERY 1 HOUR
STARTS CURRENT_TIMESTAMP
DO
BEGIN
    CALL check_inactive_users();
END;
//

DELIMITER ;
Step 6: Enable the event scheduler
sql
Copy
Edit
SET GLOBAL event_scheduler = ON;
Check if it’s running:

sql
Copy
Edit
SHOW VARIABLES LIKE 'event_scheduler';
🧪 Optional enhancements
Auto-resolve no_update alarms when a new location is inserted

Add logging of each event run (e.g., run ID, timestamp, number of alarms created)

Let me know when you're ready to repeat this on your DigitalOcean MySQL server, and I’ll help verify each step there.


✅ ALARM SYSTEM OVERVIEW
Implemented in MySQL for location-based monitoring with three use cases:

🔔 Use Case 1: Distance Violation Alarm
Goal: Trigger an alarm when a user moves beyond a configurable distance from their home_lat / home_lng.

✅ Implemented in:
AFTER INSERT trigger on locations

✅ Logic:
Get user's home location from users.home_lat / home_lng

Get per-user or global distance_threshold from user_alarm_config or alarm_config

Use ST_Distance_Sphere() to calculate distance from home

If distance exceeds threshold and no active alarm exists → insert alarm

✅ Example logic:
sql
Copy
Edit
IF distance > distance_threshold THEN
  IF NOT EXISTS (SELECT 1 FROM alarms WHERE ...) THEN
    INSERT INTO alarms (...) VALUES (...);
  END IF;
END IF;
🏥 Use Case 2: Restricted Zone Alarm
Goal: Trigger an alarm when a user enters a restricted area (e.g., near a hospital).

✅ Implemented in:
Same AFTER INSERT trigger on locations

✅ Logic:
Get global or user-specific restricted_zone_radius

Loop (or use subquery) to check if user is within this radius of any hospital

If so and no active alarm exists → insert alarm

✅ Example logic:
sql
Copy
Edit
IF EXISTS (
  SELECT 1 FROM hospitals
  WHERE ST_Distance_Sphere(...) < restricted_radius
)
AND NOT EXISTS (...) THEN
  INSERT INTO alarms (...) VALUES (...);
END IF;
⏳ Use Case 3: No Update Alarm
Goal: Trigger an alarm if a user hasn’t updated their location in a configurable time window (e.g., 3 or 9 hours)

✅ Implemented using:
A stored procedure: check_inactive_users()

A scheduled MySQL event: check_inactive_users_event

✅ Logic:
Get alarm_hours from alarm_config

For each user, find last known location timestamp

If last_update_time < NOW() - INTERVAL alarm_hours, and no active alarm → insert alarm

✅ Run every hour:
sql
Copy
Edit
CALL check_inactive_users();
✅ Summary of What’s in Production (or Ready for DigitalOcean)
Use Case	Type	Table(s) Involved	Trigger/Procedure/Event
Distance Violation	AFTER INSERT TRIGGER	locations, users, alarms, alarm_config, user_alarm_config	trg_after_location_insert
Restricted Zone	AFTER INSERT TRIGGER	locations, hospitals, alarms	trg_after_location_insert
No Update	Stored Procedure + Event	locations, alarms, alarm_config	check_inactive_users() + check_inactive_users_event
🧪 Next Steps for DigitalOcean
Let me know if you'd like me to:

Package these into a single .sql deployment script

Test all components after MySQL droplet setup

Add auto-resolution logic for all alarm types

You’re in a great position to reuse this model anywhere. Let’s deploy it next when you're ready.





✅ SQL Trigger: trg_after_location_insert
sql
Copy
Edit
USE shahencho_mydatabase;

DELIMITER //

DROP TRIGGER IF EXISTS trg_after_location_insert;
//

CREATE TRIGGER trg_after_location_insert
AFTER INSERT ON locations
FOR EACH ROW
BEGIN
  DECLARE home_lat FLOAT;
  DECLARE home_lon FLOAT;
  DECLARE distance FLOAT;
  DECLARE distance_threshold FLOAT;
  DECLARE restricted_radius FLOAT;

  -- 1. Get user's home location
  SELECT u.home_lat, u.home_lng INTO home_lat, home_lon
  FROM users u WHERE u.id = NEW.user_id;

  -- 2. Get per-user or global distance threshold
  SELECT COALESCE(
    (SELECT config_value FROM user_alarm_config 
     WHERE user_id = NEW.user_id AND config_key = 'distance_threshold'),
    (SELECT config_value FROM alarm_config 
     WHERE config_key = 'distance_threshold')
  ) INTO distance_threshold;

  -- 3. Get per-user or global restricted zone radius
  SELECT COALESCE(
    (SELECT config_value FROM user_alarm_config 
     WHERE user_id = NEW.user_id AND config_key = 'restricted_zone_radius'),
    (SELECT config_value FROM alarm_config 
     WHERE config_key = 'restricted_zone_radius')
  ) INTO restricted_radius;

  -- 4. Calculate distance from home (in meters)
  SET distance = ST_Distance_Sphere(
    POINT(NEW.lng, NEW.lat),
    POINT(home_lon, home_lat)
  );

  -- 5. Trigger distance_violation if threshold exceeded
  IF distance > distance_threshold THEN
    IF NOT EXISTS (
      SELECT 1 FROM alarms 
      WHERE user_id = NEW.user_id 
        AND alarm_type = 'distance_violation' 
        AND status = 'active'
    ) THEN
      INSERT INTO alarms (user_id, alarm_type, distance, timestamp, status)
      VALUES (NEW.user_id, 'distance_violation', distance, NOW(), 'active');
    END IF;
  END IF;

  -- 6. Trigger restricted_area alarm if near hospital
  IF EXISTS (
    SELECT 1 FROM hospitals h
    WHERE ST_Distance_Sphere(
      POINT(NEW.lng, NEW.lat),
      POINT(h.longitude, h.latitude)
    ) < restricted_radius
  ) THEN
    IF NOT EXISTS (
      SELECT 1 FROM alarms 
      WHERE user_id = NEW.user_id 
        AND alarm_type = 'restricted_area' 
        AND status = 'active'
    ) THEN
      INSERT INTO alarms (user_id, alarm_type, timestamp, status)
      VALUES (NEW.user_id, 'restricted_area', NOW(), 'active');
    END IF;
  END IF;

  -- 7. Update user's last_seen
  UPDATE users SET last_seen = NOW()
  WHERE id = NEW.user_id;

END;
//

DELIMITER ;
✅ Summary of Alarm Logic
Use Case	Alarm Type	Logic Triggered When...
Use Case 1	distance_violation	User is farther than allowed from their home location
Use Case 2	restricted_area	User is within the restricted radius of any hospital
Both alarms	Status = 'active'	Inserted only if not already active
Let me know if you’d like to add auto-resolve logic into this trigger when users return to normal zones.


	1	Providence Saint Joseph Medical Center	34.1619	-118.3089	2025-03-31 00:59:38
	2	Valley Presbyterian Hospital	34.2103	-118.4473	2025-03-31 00:59:38
	3	Northridge Hospital Medical Center	34.2286	-118.5265	2025-03-31 00:59:38
	4	Sherman Oaks Hospital	34.1516	-118.4489	2025-03-31 00:59:38
	5	Encino Hospital Medical Center	34.1566	-118.5016	2025-03-31 00:59:38
	6	Mission Community Hospital	34.2554	-118.4472	2025-03-31 00:59:38
	7	Glendale Adventist Medical Center	34.1424	-118.2552	2025-03-31 00:59:38
	8	USC Verdugo Hills Hospital	34.2158	-118.2309	2025-03-31 00:59:38
	9	Providence Holy Cross Medical Center	34.2788	-118.4654	2025-03-31 00:59:38
	10	Kaiser Permanente Panorama City Medical Center	34.2231	-118.4476	2025-03-31 00:59:38
	11	Los Angeles Community Hospital	34.0726	-118.2093	2025-03-31 00:59:38
	12	Hollywood Presbyterian Medical Center	34.0936	-118.3252	2025-03-31 00:59:38
	13	Cedars-Sinai Medical Center	34.0776	-118.3734	2025-03-31 00:59:38
	14	Children's Hospital Los Angeles	34.0938	-118.2884	2025-03-31 00:59:38
	15	Kaiser Permanente Los Angeles Medical Center	34.0988	-118.2978	2025-03-31 00:59:38
	16	Ronald Reagan UCLA Medical Center	34.0664	-118.4456	2025-03-31 00:59:38
	17	Southern California Hospital at Hollywood	34.0919	-118.3397	2025-03-31 00:59:38
	18	St. Vincent Medical Center	34.0591	-118.2736	2025-03-31 00:59:38
	19	California Hospital Medical Center	34.0336	-118.2665	2025-03-31 00:59:38
	20	Keck Hospital of USC	34.0624	-118.2057	2025-03-31 00:59:38
	21	Providence Saint Joseph Medical Center	34.1489	-118.3337	2025-03-31 01:25:21
	22	Glendale Memorial Hospital	34.1425	-118.2551	2025-03-31 01:25:21
	23	USC Verdugo Hills Hospital	34.2279	-118.2359	2025-03-31 01:25:21
	24	Adventist Health Glendale	34.1506	-118.2442	2025-03-31 01:25:21
	25	Hollywood Presbyterian Medical Center	34.0904	-118.2956	2025-03-31 01:25:21