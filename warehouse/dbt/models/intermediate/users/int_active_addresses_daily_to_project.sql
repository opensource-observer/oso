{#
  Daily active addresses to project by network
#}


SELECT
  project_id,
  from_namespace AS network,
  bucket_day,
  address_type AS user_type,
  COUNT(DISTINCT from_id) AS amount
FROM {{ ref('int_addresses_daily_activity') }}
GROUP BY 1, 2, 3, 4
