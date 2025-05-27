MODEL (
  name oso.int_first_last_commit_from_github_user,
  description 'First and last commit from a GitHub user',
  kind FULL,
  dialect trino,
  partitioned_by DAY("first_commit_time"),
  grain (
    artifact_id,
    artifact_source_id
  ),
  columns (
    artifact_id TEXT,
    artifact_source_id TEXT,
    artifact_namespace TEXT,
    artifact_name TEXT,
    first_commit_time TIMESTAMP,
    last_commit_time TIMESTAMP
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
  )
);

WITH aggregated AS (
  SELECT
    from_artifact_id AS artifact_id,
    from_artifact_source_id AS artifact_source_id,
    from_artifact_namespace AS artifact_namespace,
    from_artifact_name AS artifact_name,
    MIN(time) AS first_commit_time,
    MAX(time) AS last_commit_time,
  FROM oso.int_events__github
  WHERE event_type = 'COMMIT_CODE'
  GROUP BY
    from_artifact_id,
    from_artifact_source_id,
    from_artifact_namespace,
    from_artifact_name
)

SELECT
  artifact_source_id::TEXT,
  artifact_id::TEXT,  
  artifact_namespace::TEXT,
  artifact_name::TEXT,
  first_commit_time::TIMESTAMP,
  last_commit_time::TIMESTAMP
FROM aggregated