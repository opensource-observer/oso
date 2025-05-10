MODEL (
  name oso.int_artifacts_by_project_in_gitcoin_grants,
  kind FULL,
  dialect trino,
  description "Unifies all artifacts from the Gitcoin Grants Registry",
  audits (
    not_null(columns := (artifact_id, project_id))
  )
);

WITH all_websites AS (
  SELECT
    project_id,
    website AS artifact_source_id,
    'WWW' AS artifact_source,
    '' AS artifact_namespace,
    website AS artifact_name,
    website AS artifact_url,
    'WEBSITE' AS artifact_type
  FROM oso.stg_gitcoin__project_groups_summary
  WHERE website IS NOT NULL
),
all_twitter AS (
  SELECT
    project_id,
    CONCAT('https://x.com/', twitter) AS artifact_source_id,
    'TWITTER' AS artifact_source,
    '' AS artifact_namespace,
    twitter AS artifact_name,
    CONCAT('https://x.com/', twitter) AS artifact_url,
    'SOCIAL_HANDLE' AS artifact_type
  FROM oso.stg_gitcoin__project_groups_summary
  WHERE twitter IS NOT NULL
),
all_repository AS (
  SELECT
    project_id,
    github AS artifact_source_id,
    'GITHUB' AS artifact_source,
    @url_parts(github, 2) AS artifact_namespace,
    @url_parts(github, 3) AS artifact_name,
    github AS artifact_url,
    'REPOSITORY' AS artifact_type
  FROM oso.stg_gitcoin__project_groups_summary
  WHERE github IS NOT NULL
),
all_wallets AS (
  SELECT DISTINCT
    project_id,
    recipient_address AS artifact_source_id,
    @chain_id_name(chain_id) AS artifact_source,
    '' AS artifact_namespace,
    recipient_address AS artifact_name,
    recipient_address AS artifact_url,
    'WALLET' AS artifact_type
  FROM oso.stg_gitcoin__all_donations
  WHERE recipient_address IS NOT NULL
),
all_artifacts AS (
  SELECT
    *
  FROM all_websites
  UNION ALL
  SELECT
    *
  FROM all_twitter
  UNION ALL
  SELECT
    *
  FROM all_twitter
  UNION ALL
  SELECT
    *
  FROM all_repository
  UNION ALL
  SELECT
    *
  FROM all_wallets
), 
all_normalized_artifacts AS (
  SELECT DISTINCT
    @oso_entity_id('GITCOIN_GRANTS', '', project_id) AS project_id,
    LOWER(artifact_source_id) AS artifact_source_id,
    UPPER(artifact_source) AS artifact_source,
    LOWER(artifact_namespace) AS artifact_namespace,
    LOWER(artifact_name) AS artifact_name,
    LOWER(artifact_url) AS artifact_url,
    UPPER(artifact_type) AS artifact_type
  FROM all_artifacts
  WHERE artifact_name IS NOT NULL
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
