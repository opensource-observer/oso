MODEL (
  name metrics.int_events,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 1
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("time"), "event_type"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id)
);

select
  time,
  to_artifact_id,
  from_artifact_id,
  UPPER(event_type) as event_type,
  CAST(event_source_id as STRING) as event_source_id,
  UPPER(event_source) as event_source,
  LOWER(to_artifact_name) as to_artifact_name,
  LOWER(to_artifact_namespace) as to_artifact_namespace,
  UPPER(to_artifact_type) as to_artifact_type,
  LOWER(to_artifact_source_id) as to_artifact_source_id,
  LOWER(from_artifact_name) as from_artifact_name,
  LOWER(from_artifact_namespace) as from_artifact_namespace,
  UPPER(from_artifact_type) as from_artifact_type,
  LOWER(from_artifact_source_id) as from_artifact_source_id,
  CAST(amount as DOUBLE) as amount
from (
  select * from @oso_source('bigquery.oso.int_events__blockchain')
  where time between @start_dt and @end_dt
  union all
  select * from metrics.int_events__github
  where time between @start_dt and @end_dt
  union all
  select * from metrics.int_events__dependencies
  where time between @start_dt and @end_dt
  union all
  select * from metrics.int_events__funding
  where time between @start_dt and @end_dt 
)
