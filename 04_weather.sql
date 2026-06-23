ALTER TABLE fact_weather_event
ADD CONSTRAINT uq_weather_event UNIQUE (state_id, event_date, source);

SELECT MIN(report_date), MAX(report_date) FROM fact_outage_event;

SELECT COUNT(*) FROM fact_weather_event;