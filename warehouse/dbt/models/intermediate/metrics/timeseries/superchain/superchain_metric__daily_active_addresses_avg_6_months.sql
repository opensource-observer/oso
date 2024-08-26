{#
  config(
    materialized='ephemeral',
  )
#}

{{ metric_from_events(
    metric_name='daily_active_addresses_avg_6_months',
    metric_unit='addresses',
    metric_sql_logic='
      select
        sample_date,
        event_source,
        to_group_id,
        COUNT(distinct from_group_id) as amount
      from events
      group by
        sample_date,
        event_source,
        to_group_id
    ',
    metric_agg_func='AVG',
    metric_time_interval_value=180,
    metric_time_interval_unit='DAY',
    event_model='int_events',
    event_sources=['OPTIMISM', 'BASE', 'FRAX', 'METAL', 'MODE', 'ZORA'],
    event_types=['CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'],
    to_artifact_types=['CONTRACT'],
    from_artifact_types=['EOA'],
    to_entity_type='project',
    from_entity_type='artifact',
    missing_dates='fill_with_zero'
) }}
