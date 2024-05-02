{# 
  This model is a WIP and is not yet ready for production use.
#}

WITH user_data AS (
  SELECT
    from_id,
    MAX(rfm_recency) AS r,
    MAX(rfm_frequency) AS f,
    MAX(rfm_ecosystem) AS e
  FROM {{ ref('int_address_rfm_segments_by_project') }}
  GROUP BY 1
)

SELECT
  from_id AS user_id,
  (r > 2 AND f > 2 AND e > 2) AS is_trusted
FROM user_data
