MODEL (
  name oso.int_events_daily_to_project__defillama_trading_volume,
  description 'Daily trading volume events from DefiLlama, filtered to only include events to projects',
  kind full,
  dialect trino,
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id, project_id),
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  abp.project_id,
  events.bucket_day,
  events.event_type,
  events.event_source,
  events.event_source_id,
  events.to_artifact_id,
  events.to_artifact_namespace,
  events.to_artifact_name,
  events.from_artifact_id,
  events.from_artifact_namespace,
  events.from_artifact_name,
  events.amount
FROM oso.int_events_daily__defillama_trading_volume AS events
INNER JOIN oso.artifacts_by_project_v1 AS abp
  ON events.to_artifact_id = abp.artifact_id
