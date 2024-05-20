{% set high_activity_thresh = 100 %}
{% set med_activity_thresh = 10 %}
{% set low_activity_thresh = 1 %}

with user_txn_totals as (
  select
    events.from_artifact_id,
    events.event_source,
    events.project_id,
    time_intervals.time_interval,
    SUM(events.amount) as amount
  from {{ ref('int_events_daily_to_project') }} as events
  cross join {{ ref('int_time_intervals') }} as time_intervals
  where
    events.event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
    and events.bucket_day >= time_intervals.start_date
  group by
    events.from_artifact_id,
    events.event_source,
    events.project_id,
    time_intervals.time_interval
),

high_activity as (
  select
    project_id,
    event_source,
    time_interval,
    'high_activity_address_count' as metric,
    COUNT(distinct from_artifact_id) as amount
  from user_txn_totals
  where amount >= {{ high_activity_thresh }}
  group by
    project_id,
    event_source,
    time_interval
),

low_activity as (
  select
    project_id,
    network,
    time_interval,
    'low_activity_address_count' as metric,
    COUNT(distinct from_artifact_id) as amount
  from user_txn_totals
  where
    amount < {{ med_activity_thresh }}
    and amount >= {{ low_activity_thresh }}
  group by
    project_id,
    network,
    time_interval
),

medium_activity as (
  select
    project_id,
    network,
    time_interval,
    'medium_activity_address_count' as metric,
    COUNT(distinct from_artifact_id) as amount
  from user_txn_totals
  where
    amount < {{ high_activity_thresh }}
    and amount >= {{ med_activity_thresh }}
  group by
    project_id,
    network,
    time_interval
)

select * from high_activity
union all
select * from low_activity
union all
select * from medium_activity
