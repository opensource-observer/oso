MODEL (
  name oso.int_artifacts_by_project_in_ossd,
  kind FULL,
  dialect trino,
  partitioned_by (
    artifact_source,
    artifact_type
  ),
  grain (project_id, artifact_id),
  tags (
    'entity_category=artifact',
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH projects AS (
  SELECT
    project_id,
    websites AS websites,
    social AS social,
    github AS github,
    npm AS npm,
    blockchain AS blockchain,
    defillama AS defillama
  FROM oso.stg_ossd__current_projects
), all_websites AS (
  SELECT
    projects.project_id,
    unnested_website.url AS artifact_source_id,
    'WWW' AS artifact_source,
    '' AS artifact_namespace,
    unnested_website.url AS artifact_name,
    unnested_website.url AS artifact_url,
    'WEBSITE' AS artifact_type
  FROM projects
  CROSS JOIN UNNEST(projects.websites) AS @unnested_struct_ref(unnested_website)
), all_farcaster AS (
  SELECT
    projects.project_id,
    unnested_farcaster.url AS artifact_source_id,
    'FARCASTER' AS artifact_source,
    '' AS artifact_namespace,
    unnested_farcaster.url AS artifact_url,
    'SOCIAL_HANDLE' AS artifact_type,
    CASE
      WHEN unnested_farcaster.url LIKE 'https://warpcast.com/%'
      THEN SUBSTRING(unnested_farcaster.url, 22)
      ELSE unnested_farcaster.url
    END AS artifact_name
  FROM projects
  CROSS JOIN UNNEST(projects.social.farcaster) AS @unnested_struct_ref(unnested_farcaster)
), all_twitter AS (
  SELECT
    projects.project_id,
    unnested_twitter.url AS artifact_source_id,
    'TWITTER' AS artifact_source,
    '' AS artifact_namespace,
    unnested_twitter.url AS artifact_url,
    'SOCIAL_HANDLE' AS artifact_type,
    CASE
      WHEN unnested_twitter.url LIKE 'https://twitter.com/%'
      THEN SUBSTRING(unnested_twitter.url, 21)
      WHEN unnested_twitter.url LIKE 'https://x.com/%'
      THEN SUBSTRING(unnested_twitter.url, 15)
      ELSE unnested_twitter.url
    END AS artifact_name
  FROM projects
  CROSS JOIN UNNEST(projects.social.twitter) AS @unnested_struct_ref(unnested_twitter)
), github_repos_raw AS (
  SELECT
    projects.project_id,
    'GITHUB' AS artifact_source,
    unnested_github.url AS source_url,
    'REPOSITORY' AS artifact_type
  FROM projects
  CROSS JOIN UNNEST(projects.github) AS @unnested_struct_ref(unnested_github)
), github_repos AS (
  SELECT
    project_id,
    artifact_source,
    repos.id::VARCHAR AS artifact_source_id,
    repos.owner AS artifact_namespace,
    repos.name AS artifact_name,
    LOWER(CONCAT('https://github.com/', repos.owner, '/', repos.name))
      AS artifact_url,
    artifact_type
  FROM github_repos_raw
  INNER JOIN oso.stg_ossd__current_repositories AS repos
    ON LOWER(CONCAT('https://github.com/', repos.owner)) = LOWER(TRIM(TRAILING '/' FROM source_url))
    OR LOWER(repos.url) = LOWER(TRIM(TRAILING '/' FROM source_url))
), ossd_blockchain AS (
  SELECT
    projects.project_id,
    unnested_tag AS artifact_type,
    unnested_network AS artifact_source,
    unnested_blockchain.address AS artifact_source_id,
    '' AS artifact_namespace,
    unnested_blockchain.address AS artifact_name,
    unnested_blockchain.address AS artifact_url
  FROM projects
  CROSS JOIN UNNEST(projects.blockchain) AS @unnested_struct_ref(unnested_blockchain)
  CROSS JOIN UNNEST(unnested_blockchain.networks) AS @unnested_array_ref(unnested_network)
  CROSS JOIN UNNEST(unnested_blockchain.tags) AS @unnested_array_ref(unnested_tag)
), all_defillama AS (
  SELECT
    projects.project_id,
    LOWER(unnested_defillama.url) AS artifact_source_id,
    'DEFILLAMA' AS artifact_source,
    '' AS artifact_namespace,
    CASE
      WHEN unnested_defillama.url LIKE 'https://defillama.com/protocol/%'
      THEN SUBSTRING(unnested_defillama.url, 32)
      ELSE unnested_defillama.url
    END AS artifact_name,
    unnested_defillama.url AS artifact_url,
    'DEFILLAMA_PROTOCOL' AS artifact_type
  FROM projects
  CROSS JOIN UNNEST(projects.defillama) AS @unnested_struct_ref(unnested_defillama)
), ossd_funding AS (
  SELECT
    projects.project_id,
    projects.project_name AS artifact_source_id,
    'OSS_DIRECTORY' AS artifact_source,
    'oso' AS artifact_namespace,
    projects.project_name AS artifact_name,
    CONCAT('https://www.opensource.observer/projects/', projects.project_name)
      AS artifact_url,
    'WALLET' AS artifact_type
  FROM oso.int_projects AS projects
  WHERE projects.project_source = 'OSS_DIRECTORY'
), all_artifacts AS (
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM all_websites
  UNION ALL
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM all_farcaster
  UNION ALL
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM all_twitter
  UNION ALL
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM github_repos
  UNION ALL
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM ossd_blockchain
  UNION ALL
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM all_defillama
  UNION ALL
  SELECT
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  FROM ossd_funding
), all_normalized_artifacts AS (
  SELECT DISTINCT
    project_id,
    LOWER(artifact_source_id) AS artifact_source_id,
    UPPER(artifact_source) AS artifact_source,
    UPPER(artifact_type) AS artifact_type,
    LOWER(artifact_namespace) AS artifact_namespace,
    LOWER(artifact_name) AS artifact_name,
    LOWER(artifact_url) AS artifact_url
  FROM all_artifacts
)
SELECT
  project_id,
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name)
    AS artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type
FROM all_normalized_artifacts
