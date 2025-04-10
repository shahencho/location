(
    SELECT 'last_3h' AS period, l.*
    FROM locations l
    JOIN (
        SELECT tid, MAX(timestamp) AS max_timestamp
        FROM locations
        WHERE timestamp >= NOW() - INTERVAL 3 HOUR
        GROUP BY tid
    ) latest
    ON l.tid = latest.tid AND l.timestamp = latest.max_timestamp
)
UNION ALL
(
    SELECT 'last_6h' AS period, l.*
    FROM locations l
    JOIN (
        SELECT tid, MAX(timestamp) AS max_timestamp
        FROM locations
        WHERE timestamp >= NOW() - INTERVAL 6 HOUR
        GROUP BY tid
    ) latest
    ON l.tid = latest.tid AND l.timestamp = latest.max_timestamp
)
UNION ALL
(
    SELECT 'last_9h' AS period, l.*
    FROM locations l
    JOIN (
        SELECT tid, MAX(timestamp) AS max_timestamp
        FROM locations
        WHERE timestamp >= NOW() - INTERVAL 9 HOUR
        GROUP BY tid
    ) latest
    ON l.tid = latest.tid AND l.timestamp = latest.max_timestamp
)
UNION ALL
(
    SELECT 'last_12h' AS period, l.*
    FROM locations l
    JOIN (
        SELECT tid, MAX(timestamp) AS max_timestamp
        FROM locations
        WHERE timestamp >= NOW() - INTERVAL 12 HOUR
        GROUP BY tid
    ) latest
    ON l.tid = latest.tid AND l.timestamp = latest.max_timestamp
);
