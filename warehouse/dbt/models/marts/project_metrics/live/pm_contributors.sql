{# 
  
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

SELECT
  d.project_id,
  d.repository_source AS namespace,
  t.time_interval,
  CONCAT('CONTRIBUTORS_TOTAL') AS impact_metric,
  COUNT(DISTINCT d.from_id) AS amount
FROM {{ ref('int_devs') }} AS d
CROSS JOIN {{ ref('int_time_intervals') }} AS t
GROUP BY
  d.project_id,
  d.repository_source,
  t.time_interval
