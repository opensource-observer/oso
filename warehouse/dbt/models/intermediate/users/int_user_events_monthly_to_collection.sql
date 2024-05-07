{#
  This model aggregates user events to collections on
  a monthly basis. It is used to calculate various 
  user engagement metrics.
#}

select
  from_artifact_id,
  event_source,
  collection_id,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, month) as bucket_month,
  COUNT(distinct bucket_day) as count_days,
  SUM(amount) as total_amount
from {{ ref('int_user_events_daily_to_collection') }}
group by
  from_artifact_id,
  event_source,
  collection_id,
  event_type,
  TIMESTAMP_TRUNC(bucket_day, month)
