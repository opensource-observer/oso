{#
  config(
    materialized='ephemeral',
  )
#}

{{ metric_from_events(
    metric_name='gas_fees_sum_6_months',
    metric_unit='L2 ETH',
    metric_sql_logic='
      select
        sample_date,
        event_source,
        to_group_id,
        SUM(amount / 1e18) as amount
      from events
      group by
        sample_date,
        event_source,
        to_group_id
    ',
    metric_agg_func='SUM',
    metric_time_interval_value=180,
    metric_time_interval_unit='DAY',
    event_model='int_events',
    event_sources=['OPTIMISM', 'BASE', 'FRAX', 'METAL', 'MODE', 'ZORA'],
    event_types=['CONTRACT_INVOCATION_DAILY_L2_GAS_USED'],
    to_artifact_types=['CONTRACT'],
    from_artifact_types=['EOA', 'SAFE'],
    to_entity_type='project',
    from_entity_type='artifact',
    missing_dates='ignore'
) }}
