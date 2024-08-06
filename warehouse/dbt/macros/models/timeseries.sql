{% macro to_sql_array(string_list) %}
    {% set formatted_list = [] %}
    {% for item in string_list %}
        {% do formatted_list.append("'{}'".format(item)) %}
    {% endfor %}
    {{ return("(" ~ formatted_list | join(', ') ~ ")") }}
{% endmacro %}

{% macro timeseries_events(
  event_sources,
  event_types,
  to_artifact_types,
  from_artifact_types,
  time_interval='DAY',
  missing_dates='ignore',
  event_model='int_events'
) %}

with filtered_events as (
  select
    TIMESTAMP_TRUNC(`time`, {{ time_interval }}) as sample_date,
    from_artifact_id,
    to_artifact_id,
    event_source,
    amount
  from {{ ref(event_model) }}
  where
    event_type in {{ to_sql_array(event_types) }}    
    and event_source in {{ to_sql_array(event_sources) }}
    and to_artifact_type in {{ to_sql_array(to_artifact_types) }}
    and from_artifact_type in {{ to_sql_array(from_artifact_types) }}
    and `time` < TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), {{ time_interval }})
),

grouped_events as (
  select
    sample_date,
    from_artifact_id,
    to_artifact_id,
    event_source,
    SUM(amount) as amount
  from filtered_events
  group by
    sample_date,
    from_artifact_id,
    to_artifact_id,
    event_source
),

{% if missing_dates == "fill_with_zero" %}

  calendar as (
    select distinct
      TIMESTAMP_TRUNC(date_timestamp, {{ time_interval }}) as calendar_time
    from {{ ref('stg_utility__calendar') }}
    where TIMESTAMP(date_timestamp) <= CURRENT_TIMESTAMP()
  ),

  first_event_times as (
    select
      to_artifact_id,
      MIN(sample_date) as first_event_time
    from grouped_events
    group by to_artifact_id
  ),

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
  )

{% else %}

  timeseries_events as (
    select
      sample_date,
      from_artifact_id,
      to_artifact_id,
      event_source,
      amount
    from grouped_events
  )

{% endif %}

select
  timeseries_events.sample_date,
  timeseries_events.from_artifact_id,
  timeseries_events.to_artifact_id,
  artifacts_by_project.project_id,
  timeseries_events.event_source,
  timeseries_events.amount
from timeseries_events
inner join {{ ref('artifacts_by_project_v1')}} as artifacts_by_project
  on timeseries_events.to_artifact_id = artifacts_by_project.artifact_id

{% endmacro %}

{% macro window_events(
  agg_events_table,
  agg_func,
  window_size,
  entity_type
) %}

select
  {{ entity_type }}_id,
  sample_date,
  event_source,
  {{ agg_func }}(amount) over (
    partition by {{entity_type}}_id, event_source
    order by sample_date
    rows between {{ window_size-1 }} preceding and current row
  ) as amount
from {{ agg_events_table }}

{% endmacro %}