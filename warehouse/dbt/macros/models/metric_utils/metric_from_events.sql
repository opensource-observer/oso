{% macro metric_from_events(
    metric_name,
    metric_unit,
    metric_sql_logic,
    metric_agg_func,
    metric_time_interval_value,
    metric_time_interval_unit,
    event_model,
    event_sources,
    event_types,
    to_artifact_types,
    from_artifact_types,
    to_entity_type,
    from_entity_type,
    missing_dates
) %}

with filtered_events as (
  {{ filter_events(
      event_sources=event_sources,
      event_types=event_types,
      to_artifact_types=to_artifact_types,
      from_artifact_types=from_artifact_types,
      event_model=event_model
  ) }}
),

joined_events as (
  {{ join_events(
      to_entity_type=to_entity_type,
      from_entity_type=from_entity_type,
      filtered_event_model='filtered_events'
  ) }}
),

events as (
  {{ timebucket_events(
      metric_time_interval_unit=metric_time_interval_unit,
      missing_dates=missing_dates,
      joined_event_table='joined_events'
  ) }}
),

agg_events as (
  {{ metric_sql_logic }}
),

normalized_metrics as (
  {{ normalize_metric_model(
    metric_name=metric_name,
    metric_unit=metric_unit,
    metric_time_interval_value=metric_time_interval_value,
    metric_time_interval_unit=metric_time_interval_unit,
    agg_func=metric_agg_func,
    to_entity_type=to_entity_type,
    agg_event_table='agg_events'
  ) }}
)

select *
from normalized_metrics

{% endmacro %}