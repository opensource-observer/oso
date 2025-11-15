MODEL (
  name oso.int_pln_developer_lifecycle_monthly,
  description 'Developer lifecycle states for Protocol Labs Network developers with full/part time classification and state transitions',
  dialect trino,
  kind full,
  partitioned_by YEAR("bucket_month"),
  grain (bucket_month, developer_id, project_id),
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  tags (
    'entity_category=project',
    'entity_category=collection',
  )
);

@DEF("full_time_days", 10);
@DEF("part_time_days", 1);

-- Step 1: Get developer first and last activity months per project (full history)
WITH developer_activity_bounds AS (
  SELECT
    developer_id,
    project_id,
    MIN(bucket_month) AS first_contribution_month,
    MAX(bucket_month) AS last_contribution_month
  FROM oso.int_pln_developer_activity_monthly
  GROUP BY 1, 2
),

-- Step 2: Get all distinct months in the activity table
all_months AS (
  SELECT DISTINCT bucket_month
  FROM oso.int_pln_developer_activity_monthly
),

-- Step 3: Create complete grid of developer+project+month combinations
developer_project_month_grid AS (
  SELECT
    dab.developer_id,
    dab.project_id,
    dab.first_contribution_month,
    dab.last_contribution_month,
    m.bucket_month
  FROM developer_activity_bounds AS dab
  CROSS JOIN all_months AS m
  WHERE m.bucket_month >= dab.first_contribution_month
    AND m.bucket_month <= DATE_ADD('month', 1, dab.last_contribution_month)
),

-- Step 4: Join actual activity data
developer_month_activity AS (
  SELECT
    g.developer_id,
    g.project_id,
    g.bucket_month,
    g.first_contribution_month,
    g.last_contribution_month,
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
    last_contribution_month,
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
    last_contribution_month,
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
    last_contribution_month,
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
      -- Post-last months are churned by definition (no future activity)
      WHEN bucket_month > last_contribution_month THEN 'churned'
      -- Dormant: inactive months before last_contribution_month (pre-churn)
      WHEN is_active = 0 AND last_active_month IS NOT NULL THEN 'dormant'
      -- Engaged states based on current activity
      WHEN is_active = 1 AND activity_level = 'full_time' THEN 'engaged_full_time'
      WHEN is_active = 1 AND activity_level = 'part_time' THEN 'engaged_part_time'
      ELSE 'unknown_state'
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
    last_contribution_month,
    days_active,
    activity_level,
    is_active,
    months_since_last_active,
    current_state,
    -- LAG cannot use a window with a frame in Trino, so give it its own OVER clause
    LAG(current_state) OVER (
      PARTITION BY developer_id, project_id
      ORDER BY bucket_month
    ) AS prev_state,
    -- These aggregates can use the framed window alias
    MAX(CASE WHEN current_state = 'engaged_full_time' THEN 1 ELSE 0 END) OVER w AS had_full_time,
    MAX(CASE WHEN current_state = 'engaged_part_time' THEN 1 ELSE 0 END) OVER w AS had_part_time,
    MAX(CASE WHEN current_state = 'first_month' THEN 1 ELSE 0 END) OVER w AS had_first_month
  FROM state_tracking
  WINDOW w AS (
    PARTITION BY developer_id, project_id
    ORDER BY bucket_month
    ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
  )
),

-- Step 8b: Apply priority logic to determine highest engaged state
state_with_priority AS (
  SELECT
    developer_id,
    project_id,
    bucket_month,
    first_contribution_month,
    last_contribution_month,
    days_active,
    activity_level,
    is_active,
    months_since_last_active,
    current_state,
    prev_state,
    CASE
      WHEN had_full_time = 1 THEN 'engaged_full_time'
      WHEN had_part_time = 1 THEN 'engaged_part_time'
      WHEN had_first_month = 1 THEN 'first_month'
      ELSE NULL
    END AS highest_engaged_state
  FROM state_with_history
),

-- Step 9: Apply lifecycle labels based on state transitions
lifecycle_labels AS (
  SELECT
    developer_id,
    project_id,
    bucket_month,
    first_contribution_month,
    last_contribution_month,
    days_active,
    activity_level,
    months_since_last_active,
    prev_state,
    current_state,
    highest_engaged_state,
    -- Apply lifecycle labels according to state transition rules
    CASE
      -- First time: First month of activity
      WHEN current_state = 'first_month' THEN 'first time'
      
      -- From first_month state into engagement
      WHEN prev_state = 'first_month' AND activity_level = 'part_time' THEN 'new part time'
      WHEN prev_state = 'first_month' AND activity_level = 'full_time' THEN 'new full time'
      
      -- From engaged_part_time state
      WHEN prev_state = 'engaged_part_time' AND current_state = 'engaged_part_time' THEN 'part time'
      WHEN prev_state = 'engaged_part_time' AND current_state = 'engaged_full_time' THEN 'part time to full time'
      WHEN prev_state = 'engaged_part_time' AND current_state = 'dormant' THEN 'part time to dormant'
      
      -- From engaged_full_time state
      WHEN prev_state = 'engaged_full_time' AND current_state = 'engaged_full_time' THEN 'full time'
      WHEN prev_state = 'engaged_full_time' AND current_state = 'engaged_part_time' THEN 'full time to part time'
      WHEN prev_state = 'engaged_full_time' AND current_state = 'dormant' THEN 'full time to dormant'
      
      -- From dormant state returning to engagement
      WHEN prev_state = 'dormant' AND current_state = 'engaged_part_time' THEN 'dormant to part time'
      WHEN prev_state = 'dormant' AND current_state = 'engaged_full_time' THEN 'dormant to full time'
      
      -- Dormant months with no transition context
      WHEN current_state = 'dormant' AND prev_state = 'first_month' THEN 'first time to dormant'
      WHEN current_state = 'dormant' AND prev_state = 'dormant' THEN 'dormant'
      
      -- Churned states based on highest engaged state
      WHEN current_state = 'churned' AND highest_engaged_state = 'first_month' THEN 'churned (after first time)'
      WHEN current_state = 'churned' AND highest_engaged_state = 'engaged_part_time' THEN 'churned (after reaching part time)'
      WHEN current_state = 'churned' AND highest_engaged_state = 'engaged_full_time' THEN 'churned (after reaching full time)'
      WHEN prev_state = 'churned' AND current_state = 'churned' THEN 'churned'
      
      ELSE 'unknown'
    END AS label
  FROM state_with_priority
)

SELECT
  bucket_month,
  developer_id,
  project_id,
  label,
  days_active,
  activity_level,
  months_since_last_active,
  current_state,
  prev_state,
  highest_engaged_state,
  first_contribution_month,
  last_contribution_month
FROM lifecycle_labels
