{% set metric_name = "gas_fees_sum_6_months" %}
{% set metric_unit = "L2 ETH" %}
{% set event_sources = [
  "'OPTIMISM'", 
  "'BASE'", 
  "'FRAX'",
  "'METAL'",
  "'MODE'",
  "'ZORA'"
] %}
{% set event_types = ["'CONTRACT_INVOCATION_DAILY_L2_GAS_USED'"] %}
{% set to_types = ["'CONTRACT'"] %}
{% set from_types = ["'EOA', 'SAFE'"] %}
{% set window_interval = "DAY" %}
{% set window_size = 180 %}
{% set window_missing_dates = "ignore" %}
{% set sampling_interval = "daily" %}

with filtered_events as (
  select
    TIMESTAMP_TRUNC(`time`, {{ window_interval }}) as sample_date,
    from_artifact_id,
    to_artifact_id,
    event_source,
    amount
  from {{ ref('int_events') }}
  where
    event_source in ({{ event_sources | join(', ') }})
    and event_type in ({{ event_types | join(', ') }})
    and to_artifact_type in ({{ to_types | join(', ') }})
    and from_artifact_type in ({{ from_types | join(', ') }})
),

grouped_events as (
  select
    sample_date,
    from_artifact_id,
    to_artifact_id,
    event_source,
    SUM(amount / 1e18) as amount
  from filtered_events
  group by
    sample_date,
    from_artifact_id,
    to_artifact_id,
    event_source
),

first_event_times as (
  select
    to_artifact_id,
    MIN(sample_date) as first_event_time
  from grouped_events
  group by to_artifact_id
),

calendar as (
  select distinct
    TIMESTAMP_TRUNC(date_timestamp, {{ window_interval }}) as calendar_time
  from {{ ref('stg_utility__calendar') }}
  where TIMESTAMP(date_timestamp) <= CURRENT_TIMESTAMP()
),

{% if window_missing_dates == "fill_with_zero" %}
  timeseries_events as (
    select
      calendar.calendar_time as sample_date,
      event_dates.from_artifact_id,
      event_dates.to_artifact_id,
      event_dates.event_source,
      COALESCE(grouped_events.amount, 0) as amount
    from
      calendar
    cross join (
      select
        from_artifact_id,
        to_artifact_id,
        event_source
      from grouped_events
      group by
        from_artifact_id,
        to_artifact_id,
        event_source
    ) as event_dates
    left join grouped_events
      on calendar.calendar_time = grouped_events.sample_date
      and event_dates.from_artifact_id = grouped_events.from_artifact_id
      and event_dates.to_artifact_id = grouped_events.to_artifact_id
      and event_dates.event_source = grouped_events.event_source
    where
      calendar.calendar_time >= (
        select MIN(first_event_time)
        from first_event_times
        where first_event_times.to_artifact_id = event_dates.to_artifact_id
      )
  ),
{% else %}
  timeseries_events as (
    select
      sample_date,
      from_artifact_id,
      to_artifact_id,
      event_source,
      amount
    from grouped_events
  ),
{% endif %}

agg_events as (
  select
    events.sample_date,
    events.event_source,
    artifacts_by_project.project_id,
    SUM(events.amount) as amount
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
      rows between {{ window_size-1 }} preceding and current row
    ) as amount
  from agg_events
)

select
  project_id,
  sample_date,
  event_source,
  amount,
  '{{ metric_name }}' as metric,
  '{{ metric_unit }}' as unit
from windowed_events
