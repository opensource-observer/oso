SELECT
    @metrics_sample_date(events.bucket_day) AS metrics_sample_date,
    UPPER(events.from_artifact_namespace) AS event_source,
    events.to_artifact_id,
    '' AS from_artifact_id,
    @metric_name() AS metric,
    SUM(events.amount) / @metrics_sample_interval_length(events.bucket_day, 'day') AS amount
FROM oso.int_events_daily__defillama AS events
WHERE
    events.event_type = 'DEFILLAMA_LP_FEES'
    AND events.bucket_day BETWEEN @metrics_start('DATE') AND @metrics_end('DATE')
GROUP BY 1, 2, 3, 4, 5;
