MODEL (
  name oso.int_events__github,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 1
  ),
  start @github_incremental_start,
  cron '@daily',
  partitioned_by (DAY("time"), "event_type"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id)
);

WITH github_commits AS (
  /* noqa: ST06 */
  SELECT
    created_at AS "time",
    'COMMIT_CODE' AS event_type,
    push_id::TEXT AS event_source_id,
    'GITHUB' AS event_source,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(1)] AS to_name,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(0)] AS to_namespace,
    'REPOSITORY' AS to_type,
    repository_id::TEXT AS to_artifact_source_id,
    COALESCE(actor_login, author_email) AS from_name,
    COALESCE(actor_login, author_email) AS from_namespace,
    CASE WHEN NOT actor_login IS NULL THEN 'GIT_USER' ELSE 'GIT_EMAIL' END AS from_type,
    CASE WHEN NOT actor_login IS NULL THEN actor_id::TEXT ELSE author_email END AS from_artifact_source_id,
    1::DOUBLE AS amount
  FROM oso.stg_github__distinct_commits_resolved_mergebot
  WHERE
    created_at BETWEEN @start_dt AND @end_dt
), github_releases AS (
  /* noqa: ST06 */
  SELECT
    created_at AS "time",
    type AS event_type,
    id::TEXT AS event_source_id,
    'GITHUB' AS event_source,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(1)] AS to_name,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(0)] AS to_namespace,
    'REPOSITORY' AS to_type,
    repository_id::TEXT AS to_artifact_source_id,
    actor_login AS from_name,
    actor_login AS from_namespace,
    'GIT_USER' AS from_type,
    actor_id::TEXT AS from_artifact_source_id,
    1::DOUBLE AS amount
  FROM oso.stg_github__releases
  WHERE
    created_at BETWEEN @start_dt AND @end_dt
), github_comments AS (
  /* noqa: ST06 */
  SELECT
    event_time AS "time",
    type AS event_type,
    id::TEXT AS event_source_id,
    'GITHUB' AS event_source,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(1)] AS to_name,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(0)] AS to_namespace,
    'REPOSITORY' AS to_type,
    repository_id::TEXT AS to_artifact_source_id,
    actor_login AS from_name,
    actor_login AS from_namespace,
    'GIT_USER' AS from_type,
    actor_id::TEXT AS from_artifact_source_id,
    1::DOUBLE AS amount
  FROM oso.stg_github__comments
  WHERE
    event_time BETWEEN @start_dt AND @end_dt
), github_issues AS (
  /* noqa: ST06 */
  SELECT
    event_time AS "time",
    type AS event_type,
    id::TEXT AS event_source_id,
    'GITHUB' AS event_source,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(1)] AS to_name,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(0)] AS to_namespace,
    'REPOSITORY' AS to_type,
    repository_id::TEXT AS to_artifact_source_id,
    actor_login AS from_name,
    actor_login AS from_namespace,
    'GIT_USER' AS from_type,
    actor_id::TEXT AS from_artifact_source_id,
    1::DOUBLE AS amount
  FROM oso.stg_github__issues
  WHERE
    event_time BETWEEN @start_dt AND @end_dt
), github_pull_requests AS (
  /* noqa: ST06 */
  SELECT
    event_time AS "time",
    type AS event_type,
    id::TEXT AS event_source_id,
    'GITHUB' AS event_source,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(1)] AS to_name,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(0)] AS to_namespace,
    'REPOSITORY' AS to_type,
    repository_id::TEXT AS to_artifact_source_id,
    actor_login AS from_name,
    actor_login AS from_namespace,
    'GIT_USER' AS from_type,
    actor_id::TEXT AS from_artifact_source_id,
    1::DOUBLE AS amount
  FROM oso.stg_github__pull_requests
  WHERE
    event_time BETWEEN @start_dt AND @end_dt
), github_pull_request_merge_events AS (
  /* noqa: ST06 */
  SELECT
    event_time AS "time",
    type AS event_type,
    id::TEXT AS event_source_id,
    'GITHUB' AS event_source,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(1)] AS to_name,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(0)] AS to_namespace,
    'REPOSITORY' AS to_type,
    repository_id::TEXT AS to_artifact_source_id,
    actor_login AS from_name,
    actor_login AS from_namespace,
    'GIT_USER' AS from_type,
    actor_id::TEXT AS from_artifact_source_id,
    1::DOUBLE AS amount
  FROM oso.stg_github__pull_request_merge_events
  WHERE
    event_time BETWEEN @start_dt AND @end_dt
), github_stars_and_forks AS (
  /* noqa: ST06 */
  SELECT
    created_at AS "time",
    type AS event_type,
    id::TEXT AS event_source_id,
    'GITHUB' AS event_source,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(1)] AS to_name,
    STR_SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(0)] AS to_namespace,
    'REPOSITORY' AS to_type,
    repository_id::TEXT AS to_artifact_source_id,
    actor_login AS from_name,
    actor_login AS from_namespace,
    'GIT_USER' AS from_type,
    actor_id::TEXT AS from_artifact_source_id,
    1::DOUBLE AS amount
  FROM oso.stg_github__stars_and_forks
  WHERE
    created_at BETWEEN @start_dt AND @end_dt
), all_events AS (
  SELECT
    time,
    event_type,
    event_source_id,
    event_source,
    @oso_entity_id(event_source, to_namespace, to_name) AS to_artifact_id,
    to_name AS to_artifact_name,
    to_namespace AS to_artifact_namespace,
    to_type AS to_artifact_type,
    to_artifact_source_id,
    @oso_entity_id(event_source, from_namespace, from_name) AS from_artifact_id,
    from_name AS from_artifact_name,
    from_namespace AS from_artifact_namespace,
    from_type AS from_artifact_type,
    from_artifact_source_id,
    amount
  FROM (
    SELECT
      *
    FROM github_commits
    UNION ALL
    SELECT
      *
    FROM github_issues
    UNION ALL
    SELECT
      *
    FROM github_pull_requests
    UNION ALL
    SELECT
      *
    FROM github_pull_request_merge_events
    UNION ALL
    SELECT
      *
    FROM github_releases
    UNION ALL
    SELECT
      *
    FROM github_stars_and_forks
    UNION ALL
    SELECT
      *
    FROM github_comments
  )
)
SELECT
  time,
  to_artifact_id,
  from_artifact_id,
  UPPER(event_type) AS event_type,
  event_source_id::TEXT AS event_source_id,
  UPPER(event_source) AS event_source,
  LOWER(to_artifact_name) AS to_artifact_name,
  LOWER(to_artifact_namespace) AS to_artifact_namespace,
  UPPER(to_artifact_type) AS to_artifact_type,
  LOWER(to_artifact_source_id) AS to_artifact_source_id,
  LOWER(from_artifact_name) AS from_artifact_name,
  LOWER(from_artifact_namespace) AS from_artifact_namespace,
  UPPER(from_artifact_type) AS from_artifact_type,
  LOWER(from_artifact_source_id) AS from_artifact_source_id,
  amount::DOUBLE AS amount
FROM all_events
