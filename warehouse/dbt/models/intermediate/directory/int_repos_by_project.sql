WITH github_stats AS (
  SELECT
    to_id AS artifact_id,
    MIN(time) AS first_commit_time,
    MAX(time) AS last_commit_time,
    COUNT(DISTINCT TIMESTAMP_TRUNC(time, DAY)) AS days_with_commits_count,
    COUNT(DISTINCT from_id) AS contributors_to_repo_count
  FROM {{ ref('int_events_to_project') }}
  WHERE event_type = 'COMMIT_CODE'
  GROUP BY to_id
)

SELECT
  p.project_id,
  p.project_slug,
  p.project_name,
  r.repository_source,
  r.artifact_id,
  r.is_fork AS repo_is_fork,
  r.fork_count AS repo_fork_count,
  r.star_count AS repo_star_count,
  s.first_commit_time,
  s.last_commit_time,
  s.days_with_commits_count,
  s.contributors_to_repo_count,
  LOWER(r.name_with_owner) AS repo_name_with_owner
FROM {{ ref('stg_ossd__repositories_by_project') }} AS r
LEFT JOIN {{ ref('int_projects') }} AS p
  ON r.project_id = p.project_id
LEFT JOIN github_stats AS s
  ON r.artifact_id = s.artifact_id
WHERE r.repository_source = 'GITHUB'
