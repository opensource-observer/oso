{#
  This model is a directory of all GitHub repositories that are associated with a project.
  It includes metadata about the repository, as well as the first and last commit dates.
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

WITH github_stats AS (
  SELECT
    artifact_id,
    MIN(bucket_day) AS first_commit_date,
    MAX(bucket_day) AS last_commit_date
  FROM {{ ref('events_daily_to_artifact') }}
  WHERE event_type = 'COMMIT_CODE'
  GROUP BY artifact_id
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
  s.first_commit_date,
  s.last_commit_date,
  LOWER(r.name_with_owner) AS repo_name_with_owner
FROM {{ ref('stg_ossd__repositories_by_project') }} AS r
LEFT JOIN {{ ref('projects_v1') }} AS p
  ON r.project_id = p.project_id
LEFT JOIN github_stats AS s
  ON r.artifact_id = s.artifact_id
WHERE r.repository_source = 'GITHUB'
