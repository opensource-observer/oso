{# 
  
#}
{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}

SELECT
  d.project_id,
  d.repository_source AS namespace,
  t.time_interval,
  CONCAT('NEW_CONTRIBUTORS_TOTAL') AS impact_metric,
  COUNT(DISTINCT CASE
    WHEN DATE(d.date_first_contribution) >= DATE_TRUNC(t.start_date, MONTH)
      THEN d.from_id
  END) AS amount
FROM {{ ref('int_devs') }} AS d
CROSS JOIN {{ ref('int_time_intervals') }} AS t
GROUP BY
  d.project_id,
  d.repository_source,
  t.time_interval
