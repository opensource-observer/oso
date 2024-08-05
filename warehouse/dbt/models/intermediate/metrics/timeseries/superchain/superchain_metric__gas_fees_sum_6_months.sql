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
    "to_types": ["CONTRACT"],
    "from_types": ["EOA", "SAFE"],
    "window_interval": "DAY",
    "window_size": 180,
    "window_missing_dates": "ignore",
    "sampling_interval": "daily"
} %}

{{ timeseries_events(metric) }},

agg_events as (
  select
    events.sample_date,
    events.event_source,
    artifacts_by_project.project_id,
    SUM(events.amount / 1e18) as amount
  from timeseries_events as events
  inner join {{ ref('artifacts_by_project_v1') }} as artifacts_by_project
    on events.to_artifact_id = artifacts_by_project.artifact_id
  group by
    events.sample_date,
    events.event_source,
    artifacts_by_project.project_id
),

windowed_events as (
  select
    project_id,
    sample_date,
    event_source,
    SUM(amount) over (
      partition by project_id, event_source
      order by sample_date
      rows between {{ metric.window_size-1 }} preceding and current row
    ) as amount
  from agg_events
)

select
  project_id,
  sample_date,
  event_source,
  amount,
  '{{ metric.metric_name }}' as metric,
  '{{ metric.metric_unit }}' as unit
from windowed_events
