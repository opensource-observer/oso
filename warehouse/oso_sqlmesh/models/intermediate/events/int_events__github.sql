MODEL (
  name oso.int_events__github,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 1
  ),
  start @github_incremental_start,
  cron '@daily',
  dialect trino,
  partitioned_by (DAY("time"), "event_type"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id)
);

WITH raw_events AS (
  /* Commits */
  SELECT
    created_at AS event_time,
    'COMMIT_CODE' AS event_type,
    push_id::TEXT AS event_source_id,
    repository_name,
    repository_id,
    COALESCE(actor_login, author_email) AS actor_name,
    CASE WHEN NOT actor_login IS NULL THEN actor_id::TEXT ELSE author_email END AS actor_id,
    CASE WHEN NOT actor_login IS NULL THEN 'GIT_USER' ELSE 'GIT_EMAIL' END AS actor_type
  FROM oso.stg_github__distinct_commits_resolved_mergebot
  WHERE created_at BETWEEN @start_dt AND @end_dt

  UNION ALL

  /* Releases */
  SELECT
    created_at AS event_time,
    type AS event_type,
    id::TEXT AS event_source_id,
    repository_name,
    repository_id,
    actor_login AS actor_name,
    actor_id::TEXT AS actor_id,
    'GIT_USER' AS actor_type
  FROM oso.stg_github__releases
  WHERE created_at BETWEEN @start_dt AND @end_dt

  UNION ALL

  /* Comments, Issues, PRs, PR Merge Events */
  SELECT
    event_time,
    type AS event_type,
    id::TEXT AS event_source_id,
    repository_name,
    repository_id,
    actor_login AS actor_name,
    actor_id::TEXT AS actor_id,
    'GIT_USER' AS actor_type
  FROM oso.stg_github__comments
  WHERE event_time BETWEEN @start_dt AND @end_dt

  UNION ALL
  
  SELECT
    event_time,
    type AS event_type,
    id::TEXT AS event_source_id,
    repository_name,
    repository_id,
    actor_login AS actor_name,
    actor_id::TEXT AS actor_id,
    'GIT_USER' AS actor_type
  FROM oso.stg_github__issues
  WHERE event_time BETWEEN @start_dt AND @end_dt

  UNION ALL

  SELECT
    event_time,
    type AS event_type,
    id::TEXT AS event_source_id,
    repository_name,
    repository_id,
    actor_login AS actor_name,
    actor_id::TEXT AS actor_id,
    'GIT_USER' AS actor_type
  FROM oso.stg_github__pull_requests
  WHERE event_time BETWEEN @start_dt AND @end_dt

  UNION ALL

  SELECT
    event_time,
    type AS event_type,
    id::TEXT AS event_source_id,
    repository_name,
    repository_id,
    actor_login AS actor_name,
    actor_id::TEXT AS actor_id,
    'GIT_USER' AS actor_type
  FROM oso.stg_github__pull_request_merge_events
  WHERE event_time BETWEEN @start_dt AND @end_dt

  UNION ALL

  /* Stars and Forks */
  SELECT
    created_at AS event_time,
    type AS event_type,
    id::TEXT AS event_source_id,
    repository_name,
    repository_id,
    actor_login AS actor_name,
    actor_id::TEXT AS actor_id,
    'GIT_USER' AS actor_type
  FROM oso.stg_github__stars_and_forks
  WHERE created_at BETWEEN @start_dt AND @end_dt
), 

parsed_events AS (
  SELECT
    event_time AS time,
    UPPER(event_type) AS event_type,
    event_source_id::TEXT AS event_source_id,
    'GITHUB' AS event_source,
    LOWER(SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(1)])
      AS to_artifact_name,
    LOWER(STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(0)])
      AS to_artifact_namespace,
    'REPOSITORY' AS to_artifact_type,
    repository_id::TEXT AS to_artifact_source_id,
    actor_name AS from_artifact_name,
    actor_name AS from_artifact_namespace,
    actor_type AS from_artifact_type,
    actor_id::TEXT AS from_artifact_source_id,
    1::DOUBLE AS amount
  FROM raw_events
)

SELECT
  time,
  @oso_entity_id(event_source, to_artifact_namespace, to_artifact_name)
    AS to_artifact_id,
  @oso_entity_id(event_source, from_artifact_namespace, from_artifact_name)
    AS from_artifact_id,
  event_type,
  event_source_id,
  event_source,
  to_artifact_name,
  to_artifact_namespace,
  to_artifact_type,
  to_artifact_source_id,
  from_artifact_name,
  from_artifact_namespace,
  from_artifact_type,
  from_artifact_source_id,
  amount
FROM parsed_events
