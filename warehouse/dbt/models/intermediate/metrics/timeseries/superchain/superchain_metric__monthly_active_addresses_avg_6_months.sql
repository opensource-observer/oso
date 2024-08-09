{#
  config(
    materialized='ephemeral',
  )
#}

{% set metric = {
    "metric_name": "monthly_active_addresses_avg_6_months",
    "metric_unit": "addresses",
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
    "window_interval": "MONTH",
    "window_size": 6,
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
    COUNT(distinct artifacts_by_address.artifact_name) as amount
  from events
  inner join {{ ref('int_artifacts_by_address') }} as artifacts_by_address
    on events.from_artifact_id = artifacts_by_address.artifact_id
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
