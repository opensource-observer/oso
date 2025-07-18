MODEL (
  name oso.int_artifacts_by_project__gitcoin,
  kind FULL,
  dialect trino,
  description "Unifies all artifacts from Gitcoin",
  audits (
    not_null(columns := (artifact_id, project_id))
  )
);

WITH projects AS (
  SELECT *
  FROM oso.stg_gitcoin__project_groups_summary
  WHERE total_amount_donated_in_usd > 0
),

project_github_cleaned AS (
  SELECT
    group_id,
    SPLIT_PART(github, '?', 1) AS github
  FROM projects
  WHERE 
    github IS NOT NULL
    AND github NOT IN (
      'github',
      'github.com',
      'orgs',
      'users',
      'repositories',
      'http:',
      'https',
      'undefined',
      'none',
      '',
      'ethereum'
    )
),

github_artifacts AS (
  SELECT
    project_repos.group_id,
    all_repos.artifact_source_id,
    'GITHUB' AS artifact_source,
    all_repos.artifact_namespace,
    all_repos.artifact_name,
    all_repos.artifact_url,
    all_repos.artifact_type
  FROM project_github_cleaned AS project_repos
  CROSS JOIN oso.int_artifacts__github AS all_repos
  WHERE project_repos.github = all_repos.artifact_namespace
),

project_twitter_cleaned AS (
  SELECT
    group_id,
    twitter
  FROM projects
  WHERE
    twitter IS NOT NULL
    AND twitter NOT IN (
      '',
      'test',
      'x',
      'twitter',
      'google'
    )
),

twitter_artifacts AS (
  SELECT
    group_id,
    CONCAT('https://x.com/', twitter) AS artifact_source_id,
    'TWITTER' AS artifact_source,
    '' AS artifact_namespace,
    twitter AS artifact_name,
    CONCAT('https://x.com/', twitter) AS artifact_url,
    'SOCIAL_HANDLE' AS artifact_type
  FROM project_twitter_cleaned
),

website_artifacts AS (
  SELECT
    group_id,
    website AS artifact_source_id,
    'WWW' AS artifact_source,
    '' AS artifact_namespace,
    website AS artifact_name,
    website AS artifact_url,
    'WEBSITE' AS artifact_type
  FROM projects
  WHERE website IS NOT NULL
),

project_addresses AS (
  SELECT
    m.project_id,
    m.recipient_address AS address,
    cl.oso_chain_name AS chain
  FROM oso.stg_gitcoin__all_matching AS m
  JOIN oso.int_chainlist AS cl
    ON m.chain_id = cl.chain_id
  WHERE m.match_amount_in_usd > 0
),

address_artifacts AS (
  SELECT
    project_lookup.group_id,
    project_addresses.chain AS artifact_source,
    project_addresses.address AS artifact_source_id,
    '' AS artifact_namespace,
    project_addresses.address AS artifact_name,
    project_addresses.address AS artifact_url,
    'WALLET' AS artifact_type
  FROM project_addresses
  JOIN oso.stg_gitcoin__project_lookup AS project_lookup
    ON project_addresses.project_id = project_lookup.project_id
),

all_normalized_artifacts AS (
  SELECT
    group_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM github_artifacts
  UNION ALL
  SELECT
    group_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM twitter_artifacts
  UNION ALL
  SELECT
    group_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM website_artifacts
  UNION ALL
  SELECT
    group_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
  FROM address_artifacts
)

SELECT DISTINCT
  @oso_entity_id('GITCOIN', '', group_id) AS project_id,
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name)
   AS artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type
FROM all_normalized_artifacts
