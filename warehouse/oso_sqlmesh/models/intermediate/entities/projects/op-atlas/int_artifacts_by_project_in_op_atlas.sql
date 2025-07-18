MODEL (
  name oso.int_artifacts_by_project_in_op_atlas,
  description "Unifies all artifacts from OP Atlas, including handling cases where contracts come in via OSO and manual overrides/exclusions.",
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
    not_null(columns := (artifact_id, project_id))
  )
);

-- =============================================================================
-- BASE OP ATLAS PROJECT DATA
-- =============================================================================
WITH op_atlas_projects AS (
  SELECT
    atlas_id,
    open_source_observer_slug,
    twitter_url
  FROM oso.stg_op_atlas_project
),

-- =============================================================================
-- WEBSITE ARTIFACTS
-- =============================================================================
website_artifacts AS (
  SELECT
    stg.atlas_id,
    parsed.artifact_url AS artifact_source_id,
    parsed.artifact_source,
    parsed.artifact_namespace,
    parsed.artifact_name,
    parsed.artifact_url,
    parsed.artifact_type
  FROM oso.stg_op_atlas_project_website AS stg
  CROSS JOIN LATERAL @parse_website_artifact(stg.website_url) AS parsed
  WHERE parsed.artifact_name IS NOT NULL
),

-- =============================================================================
-- FARCASTER ARTIFACTS
-- =============================================================================
farcaster_artifacts AS (
  SELECT
    stg.atlas_id,
    parsed.artifact_url AS artifact_source_id,
    parsed.artifact_source,
    parsed.artifact_namespace,
    parsed.artifact_name,
    parsed.artifact_url,
    parsed.artifact_type
  FROM oso.stg_op_atlas_project_farcaster AS stg
  CROSS JOIN LATERAL @parse_social_handle_artifact('FARCASTER', stg.farcaster_url) AS parsed
  WHERE parsed.artifact_name IS NOT NULL
),

-- =============================================================================
-- TWITTER ARTIFACTS
-- =============================================================================
twitter_artifacts AS (
  SELECT
    op_atlas_projects.atlas_id,
    parsed.artifact_url AS artifact_source_id,
    parsed.artifact_source,
    parsed.artifact_namespace,
    parsed.artifact_name,
    parsed.artifact_url,
    parsed.artifact_type
  FROM op_atlas_projects
  CROSS JOIN LATERAL @parse_social_handle_artifact('TWITTER', op_atlas_projects.twitter_url) AS parsed
  WHERE parsed.artifact_name IS NOT NULL
),

-- =============================================================================
-- GITHUB REPOSITORY ARTIFACTS
-- =============================================================================
github_urls AS (
  SELECT
    atlas_id,
    value AS repository_url
  FROM oso.seed_op_atlas_registry_updates
  WHERE TRIM(action) = 'INCLUDE' AND artifact_type = 'GITHUB_REPOSITORY'
  UNION
  SELECT
    atlas_id,
    repository_url
  FROM oso.stg_op_atlas_project_repository
  WHERE repository_url IS NOT NULL
),
github_artifacts AS (
  SELECT
    gh_urls.atlas_id,
    gh_int.artifact_source_id,
    'GITHUB' AS artifact_source,
    parsed_url.artifact_namespace,
    parsed_url.artifact_name,
    parsed_url.artifact_url,
    parsed_url.artifact_type
  FROM github_urls AS gh_urls
  CROSS JOIN LATERAL @parse_github_repository_artifact(gh_urls.repository_url) AS parsed_url
  LEFT JOIN oso.int_artifacts__github AS gh_int
    ON gh_int.artifact_url = gh_urls.repository_url
),

-- =============================================================================
-- CONTRACT ARTIFACTS
-- =============================================================================
contract_artifacts AS (
  SELECT
    stg.atlas_id,
    parsed.artifact_name AS artifact_source_id,
    chain_name.chain_name AS artifact_source,
    parsed.artifact_namespace,
    parsed.artifact_name,
    parsed.artifact_url,
    'CONTRACT' AS artifact_type
  FROM oso.stg_op_atlas_published_contract AS stg
  JOIN oso.seed_chain_id_to_chain_name AS chain_name
    ON chain_name.chain_id = stg.chain_id
  CROSS JOIN LATERAL @parse_blockchain_artifact(stg.contract_address) AS parsed
  WHERE parsed.artifact_name IS NOT NULL
),

-- =============================================================================
-- DEPLOYER ARTIFACTS
-- =============================================================================
all_deployers AS (
  SELECT
    stg.atlas_id,
    stg.deployer_address,
    chain_name.chain_name,
    COUNT(DISTINCT stg.atlas_id) OVER (PARTITION BY stg.deployer_address, chain_name.chain_name) as project_count_for_deployer
  FROM oso.stg_op_atlas_project_contract AS stg
  JOIN oso.seed_chain_id_to_chain_name AS chain_name
    ON chain_name.chain_id = stg.chain_id
),
deployer_artifacts AS (
  SELECT
    all_deployers.atlas_id,
    parsed.artifact_name AS artifact_source_id,
    all_deployers.chain_name AS artifact_source,
    parsed.artifact_namespace,
    parsed.artifact_name,
    parsed.artifact_url,
    'DEPLOYER' AS artifact_type
  FROM all_deployers
  CROSS JOIN LATERAL @parse_blockchain_artifact(all_deployers.deployer_address) AS parsed
  WHERE all_deployers.project_count_for_deployer = 1
),

-- =============================================================================
-- DEFILLAMA ARTIFACTS
-- =============================================================================
defillama_slugs AS (
  SELECT
    stg.atlas_id,
    stg.defillama_slug
  FROM oso.stg_op_atlas_project_defillama AS stg
  LEFT JOIN oso.seed_op_atlas_registry_updates AS updates
    ON updates.atlas_id = stg.atlas_id
    AND TRIM(updates.action) = 'EXCLUDE'
    AND updates.artifact_type = 'DEFILLAMA_PROTOCOL'
  WHERE updates.value IS NULL
  UNION
  SELECT
    atlas_id,
    value AS defillama_slug
  FROM oso.seed_op_atlas_registry_updates
  WHERE
    TRIM(action) = 'INCLUDE'
    AND artifact_type = 'DEFILLAMA_PROTOCOL'
),
defillama_artifacts AS (
  SELECT
    stg.atlas_id,
    parsed.artifact_url AS artifact_source_id,
    parsed.artifact_source,
    parsed.artifact_namespace,
    parsed.artifact_name,
    parsed.artifact_url,
    parsed.artifact_type
  FROM defillama_slugs AS stg
  LEFT JOIN oso.int_defillama_protocols AS dl_child
    ON stg.defillama_slug = dl_child.parent_protocol
  CROSS JOIN LATERAL @parse_defillama_artifact(
    CASE
      WHEN dl_child.url IS NOT NULL THEN dl_child.url
      ELSE 'https://defillama.com/protocol/' || stg.defillama_slug
    END
  ) AS parsed
  WHERE parsed.artifact_name IS NOT NULL
),


-- =============================================================================
-- OSO LINKED ARTIFACTS (Contracts, Deployers, DefiLlama from OSSD)
-- =============================================================================
oso_linked_slugs AS (
  SELECT
    op.atlas_id,
    COALESCE(updates.value, op.open_source_observer_slug)
      AS open_source_observer_slug
  FROM op_atlas_projects AS op
  LEFT JOIN oso.seed_op_atlas_registry_updates AS updates
    ON updates.atlas_id = op.atlas_id
    AND TRIM(updates.action) = 'INCLUDE'
    AND updates.artifact_type = 'OSO_SLUG'
),
oso_linked_projects AS (
  SELECT DISTINCT
    op.atlas_id,
    ossd.project_id AS ossd_id
  FROM oso_linked_slugs AS op
  JOIN oso.int_projects AS ossd
    ON ossd.project_source = 'OSS_DIRECTORY'
    AND ossd.project_name = op.open_source_observer_slug
  WHERE op.open_source_observer_slug IS NOT NULL
),
oso_artifacts_for_linked_projects AS (
  SELECT
    linked.atlas_id,
    ossd_artifacts.artifact_source_id,
    ossd_artifacts.artifact_source,
    ossd_artifacts.artifact_namespace,
    ossd_artifacts.artifact_name,
    ossd_artifacts.artifact_url,
    ossd_artifacts.artifact_type
  FROM oso_linked_projects AS linked
  JOIN oso.int_artifacts_by_project_in_ossd AS ossd_artifacts
    ON linked.ossd_id = ossd_artifacts.project_id
  WHERE ossd_artifacts.artifact_type IN (
      'CONTRACT', 'DEPLOYER', 'DEFILLAMA_PROTOCOL', 'BRIDGE'
  )
),

-- =============================================================================
-- COMBINE ALL AUTO-DISCOVERED OP ATLAS ARTIFACTS
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
  SELECT * FROM contract_artifacts
  UNION ALL
  SELECT * FROM deployer_artifacts
  UNION ALL
  SELECT * FROM defillama_artifacts
  UNION ALL
  SELECT * FROM oso_artifacts_for_linked_projects
),

-- =============================================================================
-- NORMALIZE AND DEDUPLICATE
-- =============================================================================

all_normalized_artifacts AS (
  SELECT DISTINCT
    atlas_id,
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
  @oso_entity_id('OP_ATLAS', '', atlas_id) AS project_id,
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name) AS artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type,
  atlas_id
FROM all_normalized_artifacts
