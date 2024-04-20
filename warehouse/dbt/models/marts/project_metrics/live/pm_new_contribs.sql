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
  tr.time_interval,
  CONCAT('NEW_CONTRIBUTORS_TOTAL') AS impact_metric,
  COUNT(DISTINCT CASE
    WHEN DATE(d.date_first_contribution) >= DATE_TRUNC(tr.start_date, MONTH)
      THEN d.from_id
  END) AS amount
FROM {{ ref('int_devs') }} AS d
CROSS JOIN {{ ref('time_ranges') }} AS tr
GROUP BY
  d.project_id,
  d.repository_source,
  tr.time_interval
