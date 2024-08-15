{% macro timebucket_events(
  metric_time_interval_unit='DAY',
  missing_dates='ignore',
  joined_event_table='joined_events'
) %}

with bucketed_events as (
  select
    TIMESTAMP_TRUNC(time, {{ metric_time_interval_unit }}) as sample_date,
    event_source,
    to_group_id,
    from_group_id,
    SUM(amount) as amount
  from {{ joined_event_table }}
  group by 1, 2, 3, 4
)

{% if missing_dates == "fill_with_zero" %}
, calendar as (
  select distinct
    TIMESTAMP_TRUNC(date_timestamp, {{ metric_time_interval_unit }}) as calendar_time
  from {{ ref('stg_utility__calendar') }}
  where TIMESTAMP(date_timestamp) <= CURRENT_TIMESTAMP()
),

first_event_times as (
  select
    to_group_id,
    MIN(sample_date) as first_event_time
  from bucketed_events
  group by to_group_id
),

timeseries_events as (
  select
    calendar.calendar_time as sample_date,
    event_dates.event_source,
    event_dates.to_group_id,
    event_dates.from_group_id,
    COALESCE(bucketed_events.amount, 0) as amount
  from
    calendar
  cross join (
    select distinct
      event_source,
      to_group_id,
      from_group_id
    from bucketed_events
  ) as event_dates
  left join bucketed_events
    on calendar.calendar_time = bucketed_events.sample_date
    and event_dates.event_source = bucketed_events.event_source
    and event_dates.to_group_id = bucketed_events.to_group_id
    and event_dates.from_group_id = bucketed_events.from_group_id
  where
    calendar.calendar_time >= (
      select MIN(first_event_time)
      from first_event_times
      where first_event_times.to_group_id = event_dates.to_group_id
    )
)

{% else %}

, timeseries_events as (
  select
    sample_date,
    event_source,
    to_group_id,
    from_group_id,
    amount
  from bucketed_events
)

{% endif %}

select
  sample_date,
  event_source,
  to_group_id,
  from_group_id,
  amount
from timeseries_events

{% endmacro %}