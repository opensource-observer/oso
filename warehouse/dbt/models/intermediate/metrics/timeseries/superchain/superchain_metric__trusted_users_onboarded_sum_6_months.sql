{% set metric = {
    "metric_name": "trusted_users_onboarded_sum_6_months",
    "metric_unit": "trusted user addresses",
    "event_sources": [
        "OPTIMISM", 
        "BASE", 
        "FRAX",
        "METAL",
        "MODE",
        "ZORA"
    ],
    "event_types": ["CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT"],
    "to_artifact_types": ["CONTRACT"],
    "from_artifact_types": ["EOA"],
    "window_interval": "DAY",
    "window_size": 180,
    "window_missing_dates": "fill_with_zero",
    "sampling_interval": "daily"
} %}

with events as (
  {{ timeseries_events(
      metric.event_sources,
      metric.event_types,
      metric.to_artifact_types,
      metric.from_artifact_types,
      time_interval=metric.window_interval,
      missing_dates=metric.window_missing_dates
  ) }}
),

user_stats as (
  select
    addresses.address,
    trusted_users.artifact_id,
    MIN(addresses.first_active_day) as first_day
  from {{ ref('int_first_time_addresses') }} as addresses
  left join {{ ref('int_superchain_trusted_users') }} as trusted_users
    on addresses.address = trusted_users.address
  where trusted_users.is_trusted_user = true
  group by
    addresses.address,
    trusted_users.artifact_id
),

new_users as (
  select
    events.event_source,
    events.project_id,
    user_stats.address,
    MIN(events.sample_date) as onboarding_date
  from events
  inner join user_stats
    on events.from_artifact_id = user_stats.artifact_id
  where
    events.sample_date <= DATE_ADD(user_stats.first_day, interval 30 day)
  group by
    events.event_source,
    events.project_id,
    user_stats.address
),

agg_events as (
  select
    events.sample_date,
    events.event_source,
    new_users.project_id,
    COUNT(distinct new_users.address) as amount
  from events
  inner join new_users
    on
      events.sample_date = new_users.onboarding_date
      and events.event_source = new_users.event_source
      and events.to_artifact_id = new_users.project_id
  group by
    events.sample_date,
    events.event_source,
    new_users.project_id
),

windowed_events as ({{
  window_events('agg_events', 'SUM', metric.window_size, 'project')
}})

select
  project_id,
  sample_date,
  event_source,
  amount,
  '{{ metric.metric_name }}' as metric,
  '{{ metric.metric_unit }}' as unit
from windowed_events
