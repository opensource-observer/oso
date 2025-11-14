MODEL (
  name oso.int_pln_developer_lifecycle_monthly,
  description 'Developer lifecycle states for Protocol Labs Network developers with full/part time classification and state transitions',
  dialect trino,
  kind incremental_by_time_range(
    time_column bucket_month,
    batch_size 12,
    batch_concurrency 2,
    forward_only true,
    on_destructive_change warn,
    lookback 3,
    auto_restatement_cron @default_auto_restatement_cron
  ),
  start @github_incremental_start,
  cron '@monthly',
  partitioned_by MONTH("bucket_month"),
  grain (bucket_month, developer_id, project_id),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := bucket_month,
      no_gap_date_part := 'month',
    ),
  ),
  tags (
    'entity_category=project',
    'entity_category=collection',
  )
);

@DEF("full_time_days", 10);
@DEF("part_time_days", 1);

-- Step 1: Get developer first activity month per project (over full history up to @end_dt)
WITH developer_first_month AS (
  SELECT
    developer_id,
    project_id,
    MIN(bucket_month) AS first_contribution_month
  FROM oso.int_pln_developer_activity_monthly
  WHERE bucket_month <= @end_dt
  GROUP BY 1, 2
),

-- Step 2: Get all months in the incremental time range
all_months AS (
  SELECT DISTINCT bucket_month
  FROM oso.int_pln_developer_activity_monthly
  WHERE bucket_month BETWEEN @start_dt AND @end_dt
),

-- Step 3: Create complete grid of developer+project+month combinations
developer_project_month_grid AS (
  SELECT
    dfm.developer_id,
    dfm.project_id,
    dfm.first_contribution_month,
    m.bucket_month
  FROM developer_first_month AS dfm
  CROSS JOIN all_months AS m
  WHERE m.bucket_month >= dfm.first_contribution_month
),

-- Step 4: Join actual activity data
developer_month_activity AS (
  SELECT
    g.developer_id,
    g.project_id,
    g.bucket_month,
    g.first_contribution_month,
    COALESCE(a.days_active, 0) AS days_active
  FROM developer_project_month_grid AS g
  LEFT JOIN oso.int_pln_developer_activity_monthly AS a
    ON g.developer_id = a.developer_id
    AND g.project_id = a.project_id
    AND g.bucket_month = a.bucket_month
),

-- Step 5: Classify activity level based on days active
activity_classification AS (
  SELECT
    developer_id,
    project_id,
    bucket_month,
    first_contribution_month,
    days_active,
    CASE
      WHEN days_active >= @full_time_days THEN 'full_time'
      WHEN days_active >= @part_time_days THEN 'part_time'
      ELSE 'none'
    END AS activity_level,
    -- Track if developer is active this month
    CASE WHEN days_active >= @part_time_days THEN 1 ELSE 0 END AS is_active
  FROM developer_month_activity
),

-- Step 6: Track last active month and calculate state transitions
activity_windows AS (
  SELECT
    developer_id,
    project_id,
    bucket_month,
    first_contribution_month,
    days_active,
    activity_level,
    is_active,
    -- Get last active month before current month
    MAX(CASE WHEN is_active = 1 THEN bucket_month END) 
      OVER (
        PARTITION BY developer_id, project_id
        ORDER BY bucket_month
        ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
      ) AS last_active_month
  FROM activity_classification
),

-- Step 7: Calculate months since last activity and determine internal state
state_tracking AS (
  SELECT
    developer_id,
    project_id,
    bucket_month,
    first_contribution_month,
    days_active,
    activity_level,
    is_active,
    last_active_month,
    -- Calculate months since last activity
    CASE 
      WHEN last_active_month IS NULL THEN NULL
      ELSE DATE_DIFF('month', last_active_month, bucket_month)
    END AS months_since_last_active,
    -- Determine the "state" based on activity history
    CASE
      -- First month state
      WHEN bucket_month = first_contribution_month THEN 'first_month'
      -- Churned: 3+ months of inactivity
      WHEN is_active = 0 AND last_active_month IS NOT NULL
        AND DATE_DIFF('month', last_active_month, bucket_month) >= 3 THEN 'churned'
      -- Dormant: 1-2 months of inactivity (intermediate state)
      WHEN is_active = 0 AND last_active_month IS NOT NULL
        AND DATE_DIFF('month', last_active_month, bucket_month) BETWEEN 1 AND 2 THEN 'dormant'
      -- Engaged states based on current activity
      WHEN is_active = 1 AND activity_level = 'full_time' THEN 'engaged_full_time'
      WHEN is_active = 1 AND activity_level = 'part_time' THEN 'engaged_part_time'
      ELSE 'unknown'
    END AS current_state
  FROM activity_windows
),

-- Step 8: Get previous state and last engaged state for transition labeling
state_with_history AS (
  SELECT
    developer_id,
    project_id,
    bucket_month,
    first_contribution_month,
    days_active,
    activity_level,
    is_active,
    months_since_last_active,
    current_state,
    LAG(current_state) OVER (
      PARTITION BY developer_id, project_id
      ORDER BY bucket_month
    ) AS prev_state,
    MAX(
      CASE 
        WHEN current_state IN ('first_month', 'engaged_part_time', 'engaged_full_time') 
          THEN current_state 
        ELSE NULL 
      END
    ) OVER (
      PARTITION BY developer_id, project_id
      ORDER BY bucket_month
      ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
    ) AS last_engaged_state
  FROM state_tracking
),

-- Step 9: Apply lifecycle labels based on state transitions
lifecycle_labels AS (
  SELECT
    developer_id,
    project_id,
    bucket_month,
    first_contribution_month,
    days_active,
    activity_level,
    months_since_last_active,
    prev_state,
    current_state,
    last_engaged_state,
    -- Apply lifecycle labels according to state transition rules
    CASE
      -- First time: First month of activity
      WHEN current_state = 'first_month' THEN 'first_time'
      
      -- From first_month state into engagement
      WHEN prev_state = 'first_month' AND activity_level = 'part_time' THEN 'new part time'
      WHEN prev_state = 'first_month' AND activity_level = 'full_time' THEN 'new full time'
      
      -- From engaged_part_time state
      WHEN prev_state = 'engaged_part_time' AND current_state = 'engaged_part_time' THEN 'part time'
      WHEN prev_state = 'engaged_part_time' AND current_state = 'engaged_full_time' THEN 'part time to full time'
      
      -- From engaged_full_time state
      WHEN prev_state = 'engaged_full_time' AND current_state = 'engaged_full_time' THEN 'full time'
      WHEN prev_state = 'engaged_full_time' AND current_state = 'engaged_part_time' THEN 'full time to part time'
      
      -- From dormant state returning to engagement
      WHEN prev_state = 'dormant' AND current_state = 'engaged_part_time' THEN 'part time'
      WHEN prev_state = 'dormant' AND current_state = 'engaged_full_time' THEN 'full time'

      -- Dormant months get an explicit label
      WHEN current_state = 'dormant' THEN 'dormant'
      
      -- Churned states based on last engaged state
      WHEN current_state = 'churned' AND last_engaged_state = 'first_month' THEN 'churned (after first time)'
      WHEN current_state = 'churned' AND last_engaged_state = 'engaged_part_time' THEN 'churned (after reaching part time)'
      WHEN current_state = 'churned' AND last_engaged_state = 'engaged_full_time' THEN 'churned (after reaching full time)'
      
      -- Churned continuation (label will be carried forward)
      WHEN prev_state = 'churned' AND current_state = 'churned' THEN 
        NULL
      
      -- Everything else
      ELSE 'unknown'
    END AS label
  FROM state_with_history
),

-- Step 10: Carry forward churned labels (they persist until reactivation)
final_labels AS (
  SELECT
    developer_id,
    project_id,
    bucket_month,
    first_contribution_month,
    days_active,
    activity_level,
    months_since_last_active,
    prev_state,
    current_state,
    label
  FROM lifecycle_labels
),

labeled_with_carryforward AS (
  SELECT
    developer_id,
    project_id,
    bucket_month,
    first_contribution_month,
    days_active,
    activity_level,
    months_since_last_active,
    prev_state,
    CASE
      -- For churned months after the first churned month, carry forward the label
      WHEN label IS NULL AND current_state = 'churned' THEN
        LAST_VALUE(label) IGNORE NULLS OVER (
          PARTITION BY developer_id, project_id
          ORDER BY bucket_month
          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        )
      ELSE label
    END AS label
  FROM final_labels
)

SELECT
  bucket_month,
  developer_id,
  project_id,
  label,
  first_contribution_month,
  days_active,
  activity_level,
  months_since_last_active,
  prev_state
FROM labeled_with_carryforward
