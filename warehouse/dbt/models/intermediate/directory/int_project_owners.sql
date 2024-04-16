WITH ranked_repos AS (
  SELECT
    project_id,
    owner,
    star_count,
    ROW_NUMBER() OVER (
      PARTITION BY project_id ORDER BY star_count DESC
    ) AS row_number,
    COUNT(DISTINCT owner) OVER (PARTITION BY project_id) AS count_github_owners
  FROM {{ ref('stg_ossd__repositories_by_project') }}
)

SELECT
  project_id,
  count_github_owners,
  LOWER(owner) AS primary_github_owner
  --TODO: is_git_organization
FROM ranked_repos
WHERE row_number = 1
