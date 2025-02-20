MODEL (
  name metrics.stg_open_collective__deposits,
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 1
  ),
  start '2015-01-01',
  cron '@daily',
);

select
  created_at as time,
  type as event_type,
  id as event_source_id,
  'OPEN_COLLECTIVE' as event_source,
  @oso_id(
      'OPEN_COLLECTIVE',
      json_extract_scalar(to_account, '$.slug'),
      json_extract_scalar(to_account, '$.name')
  ) as to_artifact_id,
  json_extract_scalar(to_account, '$.name') as to_name,
  json_extract_scalar(to_account, '$.slug') as to_namespace,
  json_extract_scalar(to_account, '$.type') as to_type,
  json_extract_scalar(to_account, '$.id') as to_artifact_source_id,
  @oso_id(
    'OPEN_COLLECTIVE',
    json_extract_scalar(from_account, '$.slug'),
    json_extract_scalar(from_account, '$.name')
  ) as from_artifact_id,
  json_extract_scalar(from_account, '$.name') as from_name,
  json_extract_scalar(from_account, '$.slug') as from_namespace,
  json_extract_scalar(from_account, '$.type') as from_type,
  json_extract_scalar(from_account, '$.id') as from_artifact_source_id,
  ABS(CAST(json_extract_scalar(amount, '$.value') as DOUBLE)) as amount,
  json_extract_scalar(amount, '$.currency') as unit
from @oso_source('bigquery.open_collective.deposits')
