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
),

project_owners AS (
  SELECT
    project_id,
    count_github_owners,
    LOWER(owner) AS primary_github_owner
  {# TODO: is_git_organization #}
  FROM ranked_repos
  WHERE row_number = 1
)

SELECT
  p.id AS project_id,
  p.slug AS project_slug,
  {# TODO: description AS project_description #}
  p.name AS project_name,
  p.namespace AS namespace,
  po.primary_github_owner,
  po.count_github_owners,
  ARRAY_LENGTH(JSON_EXTRACT_ARRAY(p.github)) AS count_github_artifacts,
  ARRAY_LENGTH(JSON_EXTRACT_ARRAY(p.blockchain)) AS count_blockchain_artifacts,
  ARRAY_LENGTH(JSON_EXTRACT_ARRAY(p.npm)) AS count_nint_pm_artifacts
FROM {{ ref('stg_ossd__current_projects') }} AS p
LEFT JOIN project_owners AS po
  ON p.id = po.project_id
