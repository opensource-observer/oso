{#
  This model calculates the total amount of address types for each project and namespace
  for different time intervals. The time intervals are defined in the `time_intervals` table.
  The `aggregated_data` CTE calculates the total amount of events for each project and namespace
  for each time interval. The final select statement calculates the total amount of events
  for each project and namespace for each event type and time interval, creating a normalized
  table of impact metrics.
#}


{% set activity_thresh = 10 %}

with user_data as (
  select
    a.project_id,
    a.from_namespace as network,
    a.from_id,
    a.address_type,
    a.amount,
    t.time_interval,
    t.start_date,
    DATE(a.bucket_day) as bucket_day
  from {{ ref('int_addresses_daily_activity') }} as a
  cross join {{ ref('int_time_intervals') }} as t
),

user_status as (
  select
    project_id,
    network,
    time_interval,
    from_id,
    amount,
    case
      when bucket_day >= start_date then address_type
      else 'INACTIVE'
    end as address_status
  from user_data
),

user_activity_levels as (
  select
    project_id,
    network,
    time_interval,
    from_id,
    case
      when SUM(amount) >= {{ activity_thresh }} then 'HIGH_ACTIVITY'
      when
        SUM(amount) > 1
        and SUM(amount) < {{ activity_thresh }}
        then 'MEDIUM_ACTIVITY'
      else 'LOW_ACTIVITY'
    end as activity_level
  from user_status
  where address_status != 'INACTIVE'
  group by 1, 2, 3, 4
),

final_users as (
  select
    project_id,
    network,
    time_interval,
    CONCAT(address_status, '_ADDRESSES') as impact_metric,
    COUNT(distinct from_id) as amount
  from user_status
  group by 1, 2, 3, 4
  union all
  select
    project_id,
    network,
    time_interval,
    CONCAT(activity_level, '_ADDRESSES') as impact_metric,
    COUNT(distinct from_id) as amount
  from user_activity_levels
  group by 1, 2, 3, 4
)

select
  project_id,
  network,
  time_interval,
  impact_metric,
  amount
from final_users
