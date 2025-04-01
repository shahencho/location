use shahencho_mydatabase;

CREATE TABLE user_alarm_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    config_key VARCHAR(50) NOT NULL,
    config_value FLOAT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY (user_id, config_key),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE alarm_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(50) UNIQUE NOT NULL,
    config_value FLOAT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO alarm_config (config_key, config_value) VALUES
('distance_threshold', 20000),
('restricted_zone_radius', 100);
