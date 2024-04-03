{# 
  Onchain address segementation using the RFM model.
  
  RFM stands for Recency, Frequency, and Monetary Value.
  In this version, we adapt the M to represent the 
  number of projects a user has interacted with.
  
  We will consider the following metrics:
  - Recency: Days since last activity
  - Frequency: Total activity
  - Monetary Value: Project count
  
  We will then assign a segment to each user based on these
  metrics.
#}

WITH user_data AS (
  SELECT
    from_id,
    network,
    project_id,
    count_events AS total_activity,
    DATE_DIFF(CURRENT_TIMESTAMP(), date_last_txn, DAY)
      AS days_since_last_activity
  FROM {{ ref('int_addresses') }}
),

user_project_count AS (
  SELECT
    from_id,
    network,
    COUNT(DISTINCT project_id) AS project_count
  FROM user_data
  GROUP BY 1, 2
),

user_stats AS (
  SELECT
    ud.*,
    upc.project_count
  FROM user_data AS ud
  LEFT JOIN user_project_count AS upc
    ON
      ud.from_id = upc.from_id
      AND ud.network = upc.network
),

rfm_components AS (
  SELECT
    from_id,
    network,
    project_id,
    CASE
      WHEN days_since_last_activity < 7 THEN 5
      WHEN days_since_last_activity < 30 THEN 4
      WHEN days_since_last_activity < 90 THEN 3
      WHEN days_since_last_activity < 180 THEN 2
      ELSE 1
    END AS rfm_recency,
    CASE
      WHEN total_activity = 1 THEN 1
      WHEN total_activity < 10 THEN 2
      WHEN total_activity < 100 THEN 3
      WHEN total_activity < 1000 THEN 4
      ELSE 5
    END AS rfm_frequency,
    CASE
      WHEN project_count = 1 THEN 1
      WHEN project_count <= 3 THEN 2
      WHEN project_count <= 10 THEN 3
      WHEN project_count <= 30 THEN 4
      ELSE 5
    END AS rfm_ecosystem
  FROM user_stats
)

SELECT
  *,
  CASE
    WHEN rfm_frequency = 5
      THEN
        CASE
          WHEN rfm_recency = 5 THEN 'Power'
          WHEN rfm_recency = 4 THEN 'Loyal'
          WHEN rfm_recency = 3 THEN 'At risk'
          ELSE 'Churned'
        END
    WHEN rfm_frequency = 4
      THEN
        CASE
          WHEN rfm_recency >= 4 THEN 'Loyal'
          WHEN rfm_recency = 3 THEN 'At risk'
          ELSE 'Churned'
        END
    WHEN rfm_frequency = 3
      THEN
        CASE
          WHEN rfm_recency >= 4 THEN 'Promising'
          WHEN rfm_recency = 3 THEN 'Needs attention'
          ELSE 'Tourist'
        END
    WHEN rfm_frequency = 2
      THEN
        CASE
          WHEN rfm_recency >= 4 THEN 'Noob'
          ELSE 'Tourist'
        END
    WHEN rfm_frequency = 1 THEN
      CASE
        WHEN rfm_recency >= 3 THEN 'Noob'
        ELSE 'One and done'
      END
  END AS user_segment
FROM rfm_components
