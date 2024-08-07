{#
  config(
    materialized='ephemeral',
  )
#}

{% set metric = {
    "metric_name": "trusted_daily_active_users_avg_6_months",
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

agg_events as (
  select
    events.sample_date,
    events.event_source,
    events.project_id,
    COUNT(distinct trusted_users.address) as amount
  from events
  inner join {{ ref('int_superchain_trusted_users') }} as trusted_users
    on events.from_artifact_id = trusted_users.artifact_id
  where trusted_users.is_trusted_user = true
  group by
    events.sample_date,
    events.event_source,
    events.project_id
),

windowed_events as ({{
  window_events('agg_events', 'AVG', metric.window_size, 'project')
}})

select
  project_id,
  sample_date,
  event_source,
  amount,
  '{{ metric.metric_name }}' as metric,
  '{{ metric.metric_unit }}' as unit
from windowed_events
