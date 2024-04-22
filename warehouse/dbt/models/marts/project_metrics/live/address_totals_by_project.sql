{#
  This model calculates the total amount of address types for each project and namespace
  for different time intervals. The time intervals are defined in the `time_intervals` table.
  The `aggregated_data` CTE calculates the total amount of events for each project and namespace
  for each time interval. The final select statement calculates the total amount of events
  for each project and namespace for each event type and time interval, creating a normalized
  table of impact metrics.
#}


{% set activity_thresh = 10 %}

WITH user_data AS (
  SELECT
    a.project_id,
    a.from_namespace AS network,
    a.from_id,
    a.address_type,
    a.amount,
    t.time_interval,
    t.start_date,
    DATE(a.bucket_day) AS bucket_day
  FROM {{ ref('int_addresses_daily_activity') }} AS a
  CROSS JOIN {{ ref('int_time_intervals') }} AS t
),

user_status AS (
  SELECT
    project_id,
    network,
    time_interval,
    from_id,
    amount,
    CASE
      WHEN bucket_day >= start_date THEN address_type
      ELSE 'INACTIVE'
    END AS address_status
  FROM user_data
),

user_activity_levels AS (
  SELECT
    project_id,
    network,
    time_interval,
    from_id,
    CASE
      WHEN SUM(amount) >= {{ activity_thresh }} THEN 'HIGH_ACTIVITY'
      WHEN
        SUM(amount) > 1
        AND SUM(amount) < {{ activity_thresh }}
        THEN 'MEDIUM_ACTIVITY'
      ELSE 'LOW_ACTIVITY'
    END AS activity_level
  FROM user_status
  WHERE address_status != 'INACTIVE'
  GROUP BY 1, 2, 3, 4
),

final_users AS (
  SELECT
    project_id,
    network,
    time_interval,
    CONCAT(address_status, '_ADDRESSES') AS impact_metric,
    COUNT(DISTINCT from_id) AS amount
  FROM user_status
  GROUP BY 1, 2, 3, 4
  UNION ALL
  SELECT
    project_id,
    network,
    time_interval,
    CONCAT(activity_level, '_ADDRESSES') AS impact_metric,
    COUNT(DISTINCT from_id) AS amount
  FROM user_activity_levels
  GROUP BY 1, 2, 3, 4
)

SELECT
  project_id,
  network,
  time_interval,
  impact_metric,
  amount
FROM final_users
