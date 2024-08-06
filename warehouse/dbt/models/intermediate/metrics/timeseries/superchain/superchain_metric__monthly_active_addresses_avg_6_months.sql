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
    "to_types": ["CONTRACT"],
    "from_types": ["EOA"],
    "window_interval": "MONTH",
    "window_size": 6,
    "window_missing_dates": "fill_with_zero",
    "sampling_interval": "daily"
} %}

{{ timeseries_events(metric) }},

agg_events as (
  select
    events.sample_date,
    events.event_source,
    artifacts_by_project.project_id,
    COUNT(distinct artifacts_by_address.artifact_name) as amount
  from timeseries_events as events
  inner join {{ ref('artifacts_by_project_v1') }} as artifacts_by_project
    on events.to_artifact_id = artifacts_by_project.artifact_id
  inner join {{ ref('int_artifacts_by_address') }} as artifacts_by_address
    on events.from_artifact_id = artifacts_by_address.artifact_id
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
    AVG(amount) over (
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
