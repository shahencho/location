-- Insert test no_update alarms for existing users
INSERT INTO alarms (user_id, alarm_type, timestamp, status)
SELECT 
    id as user_id,
    'no_update' as alarm_type,
    NOW() as timestamp,
    'active' as status
FROM users
WHERE id IN (
    SELECT DISTINCT user_id 
    FROM locations 
    ORDER BY RAND() 
    LIMIT 5
); 