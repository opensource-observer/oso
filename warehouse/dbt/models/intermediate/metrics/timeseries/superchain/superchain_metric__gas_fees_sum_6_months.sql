{#
  config(
    materialized='ephemeral',
  )
#}

{% set metric = {
    "metric_name": "gas_fees_sum_6_months",
    "metric_unit": "L2 ETH",
    "event_sources": [
        "OPTIMISM", 
        "BASE", 
        "FRAX",
        "METAL",
        "MODE",
        "ZORA"
    ],
    "event_types": ["CONTRACT_INVOCATION_DAILY_L2_GAS_USED"],
    "to_artifact_types": ["CONTRACT"],
    "from_artifact_types": ["EOA", "SAFE"],
    "window_interval": "DAY",
    "window_size": 180,
    "window_missing_dates": "ignore",
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
    SUM(events.amount / 1e18) as amount
  from events
  group by
    events.sample_date,
    events.event_source,
    events.project_id
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
