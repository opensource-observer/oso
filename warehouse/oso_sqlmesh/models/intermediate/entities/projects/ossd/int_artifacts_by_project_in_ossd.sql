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

-- =============================================================================
-- BASE DATA PREPARATION
-- =============================================================================

WITH projects AS (
  SELECT
    project_id,
    project_name,
    websites AS websites,
    social AS social,
    github AS github,
    blockchain AS blockchain,
    defillama AS defillama
  FROM oso.stg_ossd__current_projects
),

-- =============================================================================
-- WEBSITE ARTIFACTS
-- =============================================================================

website_artifacts AS (
  SELECT
    projects.project_id,
    artifact_fields.artifact_url AS artifact_source_id,
    artifact_fields.artifact_source,
    artifact_fields.artifact_namespace,
    artifact_fields.artifact_name,
    artifact_fields.artifact_url,
    artifact_fields.artifact_type
  FROM projects
  CROSS JOIN UNNEST(projects.websites) AS @unnested_struct_ref(unnested_website)
  CROSS JOIN LATERAL @parse_website_artifact(unnested_website.url) AS artifact_fields
),

-- =============================================================================
-- SOCIAL MEDIA ARTIFACTS
-- =============================================================================

farcaster_artifacts AS (
  SELECT
    projects.project_id,
    artifact_fields.artifact_url AS artifact_source_id,
    artifact_fields.artifact_source,
    artifact_fields.artifact_namespace,
    artifact_fields.artifact_name,
    artifact_fields.artifact_url,
    artifact_fields.artifact_type
  FROM projects
  CROSS JOIN UNNEST(projects.social.farcaster) AS @unnested_struct_ref(unnested_farcaster)
  CROSS JOIN LATERAL @parse_social_handle_artifact('FARCASTER', unnested_farcaster.url) AS artifact_fields
),

twitter_artifacts AS (
  SELECT
    projects.project_id,
    artifact_fields.artifact_url AS artifact_source_id,
    artifact_fields.artifact_source,
    artifact_fields.artifact_namespace,
    artifact_fields.artifact_name,
    artifact_fields.artifact_url,
    artifact_fields.artifact_type
  FROM projects
  CROSS JOIN UNNEST(projects.social.twitter) AS @unnested_struct_ref(unnested_twitter)
  CROSS JOIN LATERAL @parse_social_handle_artifact('TWITTER', unnested_twitter.url) AS artifact_fields
),

-- =============================================================================
-- GITHUB REPOSITORY ARTIFACTS
-- =============================================================================

github_artifacts AS (
  SELECT
    projects.project_id,
    ossd_repos.artifact_source_id,
    ossd_repos.artifact_source,
    ossd_repos.artifact_namespace,
    ossd_repos.artifact_name,
    ossd_repos.artifact_url,
    ossd_repos.artifact_type
  FROM projects
  CROSS JOIN UNNEST(projects.github) AS @unnested_struct_ref(unnested_github)
  INNER JOIN oso.int_repositories__ossd AS ossd_repos
    ON unnested_github.url = ossd_repos.artifact_url
    OR unnested_github.url = ossd_repos.owner_url
),

-- =============================================================================
-- BLOCKCHAIN ARTIFACTS
-- =============================================================================

blockchain_artifacts AS (
  SELECT
    projects.project_id,
    artifact_fields.artifact_name AS artifact_source_id,
    unnested_network AS artifact_source,
    artifact_fields.artifact_namespace,
    artifact_fields.artifact_name,
    artifact_fields.artifact_url,
    unnested_tag AS artifact_type
  FROM projects
  CROSS JOIN UNNEST(projects.blockchain) AS @unnested_struct_ref(unnested_blockchain)
  CROSS JOIN UNNEST(unnested_blockchain.networks) AS @unnested_array_ref(unnested_network)
  CROSS JOIN UNNEST(unnested_blockchain.tags) AS @unnested_array_ref(unnested_tag)
  CROSS JOIN LATERAL @parse_blockchain_artifact(unnested_blockchain.address) AS artifact_fields
),

-- =============================================================================
-- DEFILLAMA PROTOCOL ARTIFACTS
-- =============================================================================

defillama_artifacts AS (
  SELECT
    projects.project_id,
    artifact_fields.artifact_url AS artifact_source_id,
    artifact_fields.artifact_source,
    artifact_fields.artifact_namespace,
    artifact_fields.artifact_name,
    artifact_fields.artifact_url,
    artifact_fields.artifact_type
  FROM projects
  CROSS JOIN UNNEST(projects.defillama) AS @unnested_struct_ref(unnested_defillama)
  CROSS JOIN LATERAL @parse_defillama_artifact(unnested_defillama.url) AS artifact_fields
),

-- =============================================================================
-- OSSD FUNDING WALLET ARTIFACTS
-- =============================================================================

ossd_funding_artifacts AS (
  SELECT
    projects.project_id,
    artifact_fields.artifact_url AS artifact_source_id,
    artifact_fields.artifact_source,
    artifact_fields.artifact_namespace,
    artifact_fields.artifact_name,
    artifact_fields.artifact_url,
    artifact_fields.artifact_type
  FROM projects
  CROSS JOIN LATERAL @create_ossd_funding_wallet_artifact(projects.project_name) AS artifact_fields
),

-- =============================================================================
-- COMBINE ALL ARTIFACT TYPES
-- =============================================================================

all_artifacts AS (
  SELECT * FROM website_artifacts
  UNION ALL
  SELECT * FROM farcaster_artifacts
  UNION ALL
  SELECT * FROM twitter_artifacts
  UNION ALL
  SELECT * FROM github_artifacts
  UNION ALL
  SELECT * FROM blockchain_artifacts
  UNION ALL
  SELECT * FROM defillama_artifacts
  UNION ALL
  SELECT * FROM ossd_funding_artifacts
),

-- =============================================================================
-- NORMALIZE AND DEDUPLICATE
-- =============================================================================

all_normalized_artifacts AS (
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

-- =============================================================================
-- FINAL OUTPUT
-- =============================================================================

SELECT
  project_id,
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name) AS artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type
FROM all_normalized_artifacts
