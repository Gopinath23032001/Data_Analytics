ALTER TABLE fact_outage_event
ADD CONSTRAINT uq_outage_event UNIQUE (station_id, unit_no, start_ts);

SELECT conname FROM pg_constraint WHERE conrelid = 'fact_outage_event'::regclass;