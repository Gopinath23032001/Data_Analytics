-- Query 1: Worst-state forced-outage ranking
SELECT s.state_name,
       COUNT(*) FILTER (WHERE oe.outage_category LIKE 'Forced%') AS forced_events,
       SUM(oe.outage_mw) FILTER (WHERE oe.outage_category LIKE 'Forced%') AS total_mw_lost
FROM fact_outage_event oe
JOIN dim_state s ON s.state_id = oe.state_id
GROUP BY s.state_name
ORDER BY forced_events DESC
LIMIT 10;

-- Query 2: Daily trend — forced events over time, all states
SELECT report_date,
       COUNT(*) FILTER (WHERE outage_category LIKE 'Forced%') AS forced_events,
       SUM(outage_mw) FILTER (WHERE outage_category LIKE 'Forced%') AS total_mw_lost
FROM fact_outage_event
GROUP BY report_date
ORDER BY report_date;

-- Query 3 (HEADLINE): Weather vs. outage correlation
WITH daily_outages AS (
    SELECT state_id, report_date,
           COUNT(*) FILTER (WHERE outage_category LIKE 'Forced%') AS forced_events,
           COALESCE(SUM(outage_mw) FILTER (WHERE outage_category LIKE 'Forced%'), 0) AS forced_mw
    FROM fact_outage_event
    GROUP BY state_id, report_date
),
joined AS (
    SELECT d.state_id, d.report_date, d.forced_events, d.forced_mw,
           w.max_temp_c, w.rainfall_mm
    FROM daily_outages d
    JOIN fact_weather_event w
      ON w.state_id = d.state_id AND w.event_date = d.report_date
)
SELECT
    ROUND(corr(max_temp_c, forced_events)::numeric, 3)  AS temp_vs_events_corr,
    ROUND(corr(max_temp_c, forced_mw)::numeric, 3)      AS temp_vs_mw_corr,
    ROUND(corr(rainfall_mm, forced_events)::numeric, 3) AS rain_vs_events_corr,
    ROUND(corr(rainfall_mm, forced_mw)::numeric, 3)     AS rain_vs_mw_corr,
    COUNT(*) AS sample_size
FROM joined;

-- Query 4: Hot-day vs. normal-day comparison
WITH daily_outages AS (
    SELECT state_id, report_date,
           COUNT(*) FILTER (WHERE outage_category LIKE 'Forced%') AS forced_events
    FROM fact_outage_event
    GROUP BY state_id, report_date
),
joined AS (
    SELECT d.forced_events, w.max_temp_c
    FROM daily_outages d
    JOIN fact_weather_event w
      ON w.state_id = d.state_id AND w.event_date = d.report_date
)
SELECT
    CASE WHEN max_temp_c >= 40 THEN 'Hot day (>=40C)' ELSE 'Normal day (<40C)' END AS day_type,
    ROUND(AVG(forced_events)::numeric, 2) AS avg_forced_events,
    COUNT(*) AS days_count
FROM joined
GROUP BY day_type;

-- Query 5: Root-cause breakdown by reason category
SELECT reason_category,
       COUNT(*) AS event_count,
       SUM(outage_mw) AS total_mw
FROM fact_outage_event
WHERE outage_category LIKE 'Forced%'
GROUP BY reason_category
ORDER BY event_count DESC;