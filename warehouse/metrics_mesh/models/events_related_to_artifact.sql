MODEL (
  name metrics.events_related_to_artifact,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 45,
    batch_concurrency 1
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (day("time"), "event_type"),
  grain (
    time,
    event_type,
    event_source,
    from_artifact_id,
    to_artifact_id,
    event_number
  )
);

WITH pr_events AS (
  SELECT 
    `number`,
    'PULL_REQUEST_OPENED' as event_type,
    actor_id,
    created_at as time,
    LOWER(actor_login) as actor_login,
    LOWER(repository_name) as repository_name,
    CAST(repository_id as STRING) as to_artifact_source_id
  FROM @oso_source.stg_github__pull_requests
  WHERE `type` = 'PULL_REQUEST_OPENED'
  AND created_at::Date BETWEEN @start_ds::Date AND @end_ds::Date
),

merge_events AS (
  SELECT
    `number`,
    'PULL_REQUEST_MERGED' as event_type,
    actor_id,
    created_at as time,
    LOWER(actor_login) as actor_login,
    LOWER(repository_name) as repository_name,
    CAST(repository_id as STRING) as to_artifact_source_id
  FROM @oso_source.stg_github__pull_request_merge_events
  WHERE created_at::Date BETWEEN @start_ds::Date AND @end_ds::Date
),

issue_events AS (
  SELECT
    `number`,
    'ISSUE_OPENED' as event_type,
    actor_id,
    created_at as time,
    LOWER(actor_login) as actor_login,
    LOWER(repository_name) as repository_name,
    CAST(repository_id as STRING) as to_artifact_source_id
  FROM @oso_source.stg_github__issues
  WHERE created_at::Date BETWEEN @start_ds::Date AND @end_ds::Date
),

comment_events AS (
  SELECT
    `number`,
    'COMMENT_ADDED' as event_type,
    actor_id,
    created_at as time,
    LOWER(actor_login) as actor_login,
    LOWER(repository_name) as repository_name,
    CAST(repository_id as STRING) as to_artifact_source_id
  FROM @oso_source.stg_github__comments
  WHERE created_at::Date BETWEEN @start_ds::Date AND @end_ds::Date
),

all_events AS (
  SELECT 
    number,
    event_type,
    actor_id,
    time,
    actor_login,
    repository_name,
    to_artifact_source_id
  FROM pr_events
  
  UNION ALL
  
  SELECT 
    number,
    event_type,
    actor_id,
    time,
    actor_login,
    repository_name,
    to_artifact_source_id
  FROM merge_events
  
  UNION ALL
  
  SELECT 
    number,
    event_type,
    actor_id,
    time,
    actor_login,
    repository_name,
    to_artifact_source_id
  FROM issue_events
  
  UNION ALL
  
  SELECT 
    number,
    event_type,
    actor_id,
    time,
    actor_login,
    repository_name,
    to_artifact_source_id
  FROM comment_events
)

SELECT
  'GITHUB' as event_source,
  event_type,
  time,
  @oso_source.oso_id('GITHUB', actor_id) as from_artifact_id,
  @oso_source.oso_id('GITHUB', to_artifact_source_id) as to_artifact_id,
  number as event_number
FROM all_events
WHERE actor_login NOT LIKE '%[bot]'
