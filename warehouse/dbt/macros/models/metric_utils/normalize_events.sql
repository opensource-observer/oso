{% macro normalize_metric_model(
  metric_name,
  metric_unit,
  metric_time_interval_value,
  metric_time_interval_unit,
  agg_func='SUM',
  to_entity_type='project',
  agg_event_table='agg_events'
) %}


with calendar as (
  select distinct
    TIMESTAMP_TRUNC(date_timestamp, {{ metric_time_interval_unit }}) as calendar_time
  from {{ ref('stg_utility__calendar') }}
  where TIMESTAMP(date_timestamp) <= CURRENT_TIMESTAMP()
),
first_event_times as (
  select
    to_group_id,
    MIN(sample_date) as first_event_time
  from {{ agg_event_table }}
  group by to_group_id
),
timeseries_events as (
  select
    calendar.calendar_time as sample_date,
    event_dates.event_source,
    event_dates.to_group_id,
    COALESCE({{ agg_event_table }}.amount, 0) as amount
  from
    calendar
  cross join (
    select distinct
      event_source,
      to_group_id
    from {{ agg_event_table }}
  ) as event_dates
  left join {{ agg_event_table }}
    on calendar.calendar_time = {{ agg_event_table }}.sample_date
    and event_dates.event_source = {{ agg_event_table }}.event_source
    and event_dates.to_group_id = {{ agg_event_table }}.to_group_id
  where
    calendar.calendar_time >= (
      select MIN(first_event_time)
      from first_event_times
      where first_event_times.to_group_id = event_dates.to_group_id
    )
)

select
  to_group_id as {{ to_entity_type }}_id,
  sample_date,
  event_source,
  '{{ metric_name }}' as metric,
  '{{ metric_unit }}' as unit,
  {{ agg_func }}(amount) over (
    partition by to_group_id, event_source
    order by sample_date
    rows between {{ metric_time_interval_value-1 }} preceding and current row
  ) as amount
from timeseries_events

{% endmacro %}