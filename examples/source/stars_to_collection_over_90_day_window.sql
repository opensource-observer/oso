SELECT
  @METRICS_SAMPLE_DATE("events"."bucket_day") AS "metrics_sample_date",
  "events"."event_source" AS "event_source",
  "projects_by_collection_v1"."collection_id" AS "to_collection_id",
  '' AS "from_artifact_id",
  CONCAT('stars', '_over_90_day_window') AS "metric",
  SUM("events"."amount") AS "amount"
FROM "oso"."int_events_daily_to_artifact" AS "events"
INNER JOIN "oso"."artifacts_by_project_v1" AS "artifacts_by_project_v1"
  ON "events"."to_artifact_id" = "artifacts_by_project_v1"."artifact_id"
INNER JOIN "oso"."projects_by_collection_v1" AS "projects_by_collection_v1"
  ON "artifacts_by_project_v1"."project_id" = "projects_by_collection_v1"."project_id"
WHERE
  "events"."event_type" IN ('STARRED')
  AND "events"."bucket_day" BETWEEN @METRICS_START('DATE') AND @METRICS_END('DATE')
GROUP BY
  @METRICS_SAMPLE_DATE("events"."bucket_day"),
  CONCAT('stars', '_over_90_day_window'),
  4,
  "projects_by_collection_v1"."collection_id",
  "events"."event_source"