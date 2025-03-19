SELECT
  @METRICS_SAMPLE_DATE("events"."bucket_day") AS "metrics_sample_date",
  "events"."event_source" AS "event_source",
  "events"."to_artifact_id" AS "to_artifact_id",
  '' AS "from_artifact_id",
  CONCAT('stars', '_over_90_day_window') AS "metric",
  SUM("events"."amount") AS "amount"
FROM "oso"."int_events_daily_to_artifact" AS "events"
WHERE
  "events"."event_type" IN ('STARRED')
  AND "events"."bucket_day" BETWEEN @METRICS_START('DATE') AND @METRICS_END('DATE')
GROUP BY
  @METRICS_SAMPLE_DATE("events"."bucket_day"),
  CONCAT('stars', '_over_90_day_window'),
  4,
  "events"."to_artifact_id",
  "events"."event_source"