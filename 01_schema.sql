-- 1. Dimension Tables
CREATE TABLE dim_state (
    state_id        SERIAL PRIMARY KEY,
    state_name      VARCHAR(50) UNIQUE NOT NULL,
    region          VARCHAR(20),        
    is_ut           BOOLEAN DEFAULT FALSE
);
 
CREATE TABLE dim_station (
    station_id      SERIAL PRIMARY KEY,
    station_name    VARCHAR(100) NOT NULL,
    state_id        INT REFERENCES dim_state(state_id),
    station_type    VARCHAR(20),        
    sector          VARCHAR(20),       
    monitored_capacity_mw NUMERIC(10,2),
    UNIQUE(station_name, state_id)
);
-- 2. Fact Tables
 
CREATE TABLE fact_outage_event (
    event_id           BIGSERIAL PRIMARY KEY,
    station_id         INT REFERENCES dim_station(station_id),
    state_id           INT REFERENCES dim_state(state_id),
    unit_no            INT,
    outage_category    VARCHAR(20),     
    outage_mw          NUMERIC(10,2),
    start_ts           TIMESTAMP NOT NULL,
    expected_return_ts TIMESTAMP,
    actual_return_ts   TIMESTAMP,
    reason_raw         TEXT,
    reason_category    VARCHAR(40),   
    report_date        DATE NOT NULL,
    ingested_at        TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_outage_station_date ON fact_outage_event(station_id, report_date);
CREATE INDEX idx_outage_state_date ON fact_outage_event(state_id, report_date);
 
CREATE TABLE fact_weather_event (
    weather_event_id  SERIAL PRIMARY KEY,
    state_id          INT REFERENCES dim_state(state_id),
    event_type        VARCHAR(30),      
    event_date        DATE NOT NULL,
    severity          VARCHAR(20),
    max_temp_c        NUMERIC(4,1),
    rainfall_mm        NUMERIC(6,1),
    source            VARCHAR(30)       
);
 
CREATE TABLE fact_supply_position (
    supply_id         SERIAL PRIMARY KEY,
    state_id          INT REFERENCES dim_state(state_id),
    period_month      DATE NOT NULL,    
    requirement_mu    NUMERIC(10,2),    
    availability_mu   NUMERIC(10,2),
    shortfall_mu      NUMERIC(10,2),
    shortfall_pct     NUMERIC(5,2)
);
 
 
CREATE VIEW v_outage_duration AS
SELECT
    event_id, station_id, state_id, outage_category, reason_category,
    start_ts,
    COALESCE(actual_return_ts, expected_return_ts) AS resolved_ts,
    EXTRACT(EPOCH FROM (COALESCE(actual_return_ts, expected_return_ts)
             - start_ts)) / 3600 AS duration_hours
FROM fact_outage_event;