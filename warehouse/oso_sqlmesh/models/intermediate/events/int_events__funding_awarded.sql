MODEL (
  name oso.int_events__funding_awarded,
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 90,
    batch_concurrency 1
  ),
  start @funding_incremental_start,
  cron '@daily',
  partitioned_by ( DAY("time"), "event_type" ),
  grain ( time, event_source, from_artifact_name, to_artifact_name ),
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  )
);

SELECT
  f.funding_date AS time,
  f.funding_source AS event_source,
  'FUNDING_AWARDED' AS event_type,
  f.to_project_name AS to_artifact_name,
  f.funding_namespace AS to_artifact_namespace,
  @oso_entity_id(f.funding_source, f.funding_namespace, f.to_project_name) as to_artifact_id,
  f.grant_pool_name AS from_artifact_name,
  f.from_funder_name AS from_artifact_namespace,
  @oso_entity_id(f.funding_source, f.from_funder_name, f.grant_pool_name) as from_artifact_id,
  f.amount AS amount
FROM oso.stg_ossd__current_funding AS f
