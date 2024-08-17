{{
  config(
    materialized='ephemeral'
  )
}}

select
  from_artifact_id as developer_id,
  to_artifact_id,
  event_source,
  bucket_day,
  CAST(SUM(amount) > 0 as int64) as commit_count
from {{ ref('int_events_daily_to_artifact') }}
where event_type = 'COMMIT_CODE'
group by
  from_artifact_id,
  to_artifact_id,
  event_source,
  bucket_day
