SELECT
  project_slug,
  segment_type,
  bucket_month,
  SUM(amount) AS amount
FROM 
  (
    SELECT * FROM {{ ref('devs') }}
    UNION ALL
    SELECT * FROM {{ ref('users') }}
  ) combined_data
GROUP BY
  project_slug,
  segment_type,
  bucket_month