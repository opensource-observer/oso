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
            JSON_VALUE(to_account, '$.slug'),
            JSON_VALUE(to_account, '$.name')
        ) as to_artifact_id,
        JSON_VALUE(to_account, '$.name') as to_name,
        JSON_VALUE(to_account, '$.slug') as to_namespace,
        JSON_VALUE(to_account, '$.type') as to_type,
        JSON_VALUE(to_account, '$.id') as to_artifact_source_id,
        @oso_id(
          'OPEN_COLLECTIVE',
          JSON_VALUE(from_account, '$.slug'),
          JSON_VALUE(from_account, '$.name')
        ) as from_artifact_id,
        JSON_VALUE(from_account, '$.name') as from_name,
        JSON_VALUE(from_account, '$.slug') as from_namespace,
        JSON_VALUE(from_account, '$.type') as from_type,
        JSON_VALUE(from_account, '$.id') as from_artifact_source_id,
        ABS(CAST(JSON_VALUE(amount, '$.value') as DOUBLE)) as amount
    from @oso_source('bigquery.oso.stg_open_collective__expenses')
    where JSON_VALUE(amount, '$.currency') = 'USD'
),

open_collective_deposits as (
    select
        created_at as time,
        type as event_type,
        id as event_source_id,
        'OPEN_COLLECTIVE' as event_source,
        @oso_id(
            'OPEN_COLLECTIVE',
            JSON_VALUE(to_account, '$.slug'),
            JSON_VALUE(to_account, '$.name')
        ) as to_artifact_id,
        JSON_VALUE(to_account, '$.name') as to_name,
        JSON_VALUE(to_account, '$.slug') as to_namespace,
        JSON_VALUE(to_account, '$.type') as to_type,
        JSON_VALUE(to_account, '$.id') as to_artifact_source_id,
        @oso_id(
          'OPEN_COLLECTIVE',
          JSON_VALUE(from_account, '$.slug'),
          JSON_VALUE(from_account, '$.name')
        ) as from_artifact_id,
        JSON_VALUE(from_account, '$.name') as from_name,
        JSON_VALUE(from_account, '$.slug') as from_namespace,
        JSON_VALUE(from_account, '$.type') as from_type,
        JSON_VALUE(from_account, '$.id') as from_artifact_source_id,
        ABS(CAST(JSON_VALUE(amount, '$.value') as DOUBLE)) as amount
    from @oso_source('bigquery.oso.stg_open_collective__deposits')
    where JSON_VALUE(amount, '$.currency') = 'USD'
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
