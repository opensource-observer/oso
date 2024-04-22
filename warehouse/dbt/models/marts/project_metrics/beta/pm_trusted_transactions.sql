{#
  WIP: Still in Development
  Count the number of transaction from trusted users
#}
{{ 
  config(meta = {
    'sync_to_cloudsql': False
  }) 
}}

SELECT
  e.project_id,
  e.from_namespace AS namespace,
  t.time_interval,
  'TRUSTED_TRANSACTIONS_TOTAL' AS impact_metric,
  SUM(e.amount) AS amount
FROM {{ ref('int_events_to_project') }} AS e
CROSS JOIN {{ ref('int_time_intervals') }} AS t
WHERE
  DATE(e.time) >= t.start_date
  AND e.from_id IN (
    SELECT user_id
    FROM {{ ref('users') }}
    WHERE is_trusted = TRUE
  )
  AND e.event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
GROUP BY
  e.project_id,
  e.from_namespace,
  t.time_interval
