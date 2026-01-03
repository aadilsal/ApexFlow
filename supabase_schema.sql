-- 0. Users Table (Custom Auth)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 1. Telemetry Sessions Table
CREATE TABLE telemetry_sessions (
    id TEXT PRIMARY KEY,
    track TEXT NOT NULL,
    date DATE NOT NULL,
    driver TEXT NOT NULL,
    laptime TEXT NOT NULL,
    fuel FLOAT NOT NULL,
    temp INTEGER NOT NULL,
    sectors JSONB NOT NULL
);

-- 2. Predictions Table
CREATE TABLE predictions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    input_data JSONB NOT NULL,
    predicted_time FLOAT NOT NULL,
    confidence_upper FLOAT NOT NULL,
    confidence_lower FLOAT NOT NULL,
    inference_time FLOAT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Model Versions Table
CREATE TABLE model_versions (
    name TEXT PRIMARY KEY,
    mae FLOAT NOT NULL,
    rmse FLOAT NOT NULL,
    accuracy INTEGER NOT NULL,
    is_production BOOLEAN DEFAULT FALSE
);

-- 4. System Health Table
CREATE TABLE system_health (
    name TEXT PRIMARY KEY,
    latency INTEGER NOT NULL,
    error INTEGER NOT NULL
);

-- 5. Drift Metrics Table
CREATE TABLE drift_metrics (
    feature TEXT PRIMARY KEY,
    score FLOAT NOT NULL
);

-- 6. System Summary Table (Singleton)
CREATE TABLE system_summary (
    id INTEGER PRIMARY KEY DEFAULT 1,
    status TEXT NOT NULL,
    drift_level TEXT NOT NULL,
    cpu_usage TEXT NOT NULL,
    throughput TEXT NOT NULL,
    active_session TEXT NOT NULL,
    avg_lap_delta TEXT NOT NULL,
    confidence_score TEXT NOT NULL,
    CONSTRAINT singleton_check CHECK (id = 1)
);

-- Seed Data for Testing
INSERT INTO model_versions (name, mae, rmse, accuracy, is_production) VALUES
('v1.0.1', 0.12, 0.18, 94, false),
('v1.0.2', 0.11, 0.17, 95, false),
('v1.2.0', 0.08, 0.14, 97, false),
('v1.3.4', 0.042, 0.09, 99, true);

INSERT INTO system_health (name, latency, error) VALUES
('09:00', 45, 0),
('10:00', 52, 0),
('11:00', 48, 1),
('12:00', 60, 0),
('13:00', 42, 0),
('14:00', 44, 0);

INSERT INTO drift_metrics (feature, score) VALUES
('Fuel', 0.12),
('Tyre', 0.45),
('Temp', 0.22),
('Wind', 0.08),
('Downforce', 0.55);

INSERT INTO system_summary (id, status, drift_level, cpu_usage, throughput, active_session, avg_lap_delta, confidence_score) VALUES
(1, 'Healthy', 'Low', '24%', '1.2k req/s', 'Grand Prix', '+0.124', '98.2%');

INSERT INTO telemetry_sessions (id, track, date, driver, laptime, fuel, temp, sectors) VALUES
('2026-BHR-R', 'Bahrain', '2026-03-02', 'VER', '1:32.456', 12.5, 34, '["28.1", "39.2", "25.1"]'),
('2026-SAU-R', 'Saudi Arabia', '2026-03-09', 'PER', '1:29.872', 15.0, 31, '["27.4", "38.1", "24.3"]'),
('2026-AUS-R', 'Australia', '2026-03-23', 'HAM', '1:18.123', 10.2, 28, '["24.2", "32.1", "21.8"]');
