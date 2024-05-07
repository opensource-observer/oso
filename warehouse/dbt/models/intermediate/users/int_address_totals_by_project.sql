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
    int_addresses_daily_activity.project_id,
    int_addresses_daily_activity.event_source,
    int_addresses_daily_activity.from_artifact_id,
    int_addresses_daily_activity.address_type,
    int_addresses_daily_activity.amount,
    int_time_intervals.time_interval,
    int_time_intervals.start_date,
    DATE(int_addresses_daily_activity.bucket_day) as bucket_day
  from {{ ref('int_addresses_daily_activity') }}
  left join {{ ref('int_addresses_to_project') }}
    on
      int_addresses_daily_activity.from_artifact_id
      = int_addresses_to_project.artifact_id
      and int_addresses_daily_activity.project_id
      = int_addresses_to_project.project_id
  cross join {{ ref('int_time_intervals') }}
),

user_status as (
  select
    project_id,
    event_source,
    time_interval,
    from_artifact_id,
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
    event_source,
    time_interval,
    from_artifact_id,
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
  group by
    project_id,
    event_source,
    time_interval,
    from_artifact_id
),

final_users as (
  select
    project_id,
    event_source,
    time_interval,
    CONCAT(address_status, '_ADDRESSES') as impact_metric,
    COUNT(distinct from_artifact_id) as amount
  from user_status
  group by
    project_id,
    event_source,
    time_interval,
    address_status
  union all
  select
    project_id,
    event_source,
    time_interval,
    CONCAT(activity_level, '_ADDRESSES') as impact_metric,
    COUNT(distinct from_artifact_id) as amount
  from user_activity_levels
  group by
    project_id,
    event_source,
    time_interval,
    activity_level
)

select
  project_id,
  event_source,
  time_interval,
  impact_metric,
  amount
from final_users
