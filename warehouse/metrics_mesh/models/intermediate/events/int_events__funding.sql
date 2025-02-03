MODEL (
  name metrics.int_events__funding,
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 90,
    batch_concurrency 1
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("time"), "event_type"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id)
);

with open_collective_expenses as (
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
        ABS(CAST(json_extract_scalar(amount, '$.value') as DOUBLE)) as amount
    from @oso_source('bigquery.oso.stg_open_collective__expenses')
    where json_extract_scalar(amount, '$.currency') = 'USD'
      and created_at between @start_dt and @end_dt
),

open_collective_deposits as (
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
        ABS(CAST(json_extract_scalar(amount, '$.value') as DOUBLE)) as amount
    from @oso_source('bigquery.oso.stg_open_collective__deposits')
    where json_extract_scalar(amount, '$.currency') = 'USD'
      and created_at between @start_dt and @end_dt
),

all_funding_events as (
    select * from open_collective_expenses
    union all
    select * from open_collective_deposits
)

select
    time,
    to_artifact_id,
    from_artifact_id,
    UPPER(event_type) as event_type,
    CAST(event_source_id as STRING) as event_source_id,
    UPPER(event_source) as event_source,
    LOWER(to_name) as to_artifact_name,
    LOWER(to_namespace) as to_artifact_namespace,
    UPPER(to_type) as to_artifact_type,
    LOWER(to_artifact_source_id) as to_artifact_source_id,
    LOWER(from_name) as from_artifact_name,
    LOWER(from_namespace) as from_artifact_namespace,
    UPPER(from_type) as from_artifact_type,
    LOWER(from_artifact_source_id) as from_artifact_source_id,
    CAST(amount as DOUBLE) as amount
from all_funding_events
