{#
  config(
    materialized='ephemeral',
  )
#}

{% set metric_sql_logic %}
  with user_stats as (
    select
      addresses.address,
      trusted_users.artifact_id,
      MIN(addresses.first_active_day) as first_day
    from {{ ref('int_first_time_addresses') }} as addresses
    left join {{ ref('int_superchain_trusted_users') }} as trusted_users
      on addresses.address = trusted_users.address
    where trusted_users.is_trusted_user = true
    group by
      addresses.address,
      trusted_users.artifact_id
  ),

  new_users as (
    select
      events.event_source,
      events.to_group_id as group_id,
      user_stats.address,
      MIN(events.sample_date) as onboarding_date
    from events
    inner join user_stats
      on events.from_group_id = user_stats.artifact_id
    where
      events.sample_date <= DATE_ADD(user_stats.first_day, interval 30 day)
      and events.amount > 0
    group by
      events.event_source,
      events.to_group_id,
      user_stats.address
  )

  select
    events.sample_date,
    events.event_source,
    new_users.group_id as to_group_id,
    COUNT(distinct
      case when events.sample_date = new_users.onboarding_date
      then new_users.address
    end) as amount
  from events
  inner join new_users
    on
      events.event_source = new_users.event_source
      and events.to_group_id = new_users.group_id
  group by
    events.sample_date,
    events.event_source,
    new_users.group_id
{% endset %}

{{ metric_from_events(
    metric_name='trusted_users_onboarded_sum_6_months',
    metric_unit='trusted user addresses',
    metric_sql_logic=metric_sql_logic,
    metric_agg_func='SUM',
    metric_time_interval_value=180,
    metric_time_interval_unit='DAY',
    event_model='int_events',
    event_sources=['OPTIMISM', 'BASE', 'FRAX', 'METAL', 'MODE', 'ZORA'],
    event_types=['CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'],
    to_artifact_types=['CONTRACT'],
    from_artifact_types=['EOA'],
    to_entity_type='project',
    from_entity_type='artifact',
    missing_dates='ignore'
) }}
