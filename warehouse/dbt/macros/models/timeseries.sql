{% macro to_sql_array(string_list) %}
    {% set formatted_list = [] %}
    {% for item in string_list %}
        {% do formatted_list.append("'{}'".format(item)) %}
    {% endfor %}
    {{ return("(" ~ formatted_list | join(', ') ~ ")") }}
{% endmacro %}

{% macro timeseries_events(metric) %}

with filtered_events as (
  select
    TIMESTAMP_TRUNC(`time`, {{ metric.window_interval }}) as sample_date,
    from_artifact_id,
    to_artifact_id,
    event_source,
    amount
  from {{ ref('int_events') }}
  where
    event_type in {{ to_sql_array(metric.event_types) }}    
    and event_source in {{ to_sql_array(metric.event_sources) }}
    and to_artifact_type in {{ to_sql_array(metric.to_types) }}
    and from_artifact_type in {{ to_sql_array(metric.from_types) }}
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

{% if metric.window_missing_dates == "fill_with_zero" %}

  calendar as (
    select distinct
      TIMESTAMP_TRUNC(date_timestamp, {{ metric.window_interval }}) as calendar_time
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

{% endmacro %}
