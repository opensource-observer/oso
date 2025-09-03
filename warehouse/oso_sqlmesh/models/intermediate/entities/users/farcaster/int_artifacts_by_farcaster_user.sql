MODEL (
  name oso.int_artifacts_by_farcaster_user,
  kind FULL,
  description "EVM addresses linked to Farcaster IDs",
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH farcaster_addresses AS (
  SELECT DISTINCT
    addresses.farcaster_id,
    addresses.address,
    chains.chain_name
  FROM oso.stg_farcaster__addresses AS addresses
  CROSS JOIN oso.seed_chain_id_to_chain_name AS chains
  WHERE LENGTH(addresses.address) = 42
),

custody_addresses AS (
  SELECT DISTINCT
    farcaster_id,
    custody_address AS address,
    'OPTIMISM' AS chain_name
  FROM oso.stg_farcaster__profiles
  WHERE custody_address IS NOT NULL
),

all_addresses AS (
  SELECT *
  FROM farcaster_addresses
  UNION ALL
  SELECT *
  FROM custody_addresses
),

artifacts_by_user AS (
  SELECT
    profiles.farcaster_id AS user_source_id,
    'FARCASTER' AS user_source,
    '' AS user_namespace,
    profiles.farcaster_id::VARCHAR AS user_name,
    profiles.username AS display_name,
    UPPER(all_addresses.chain_name) AS artifact_source,
    '' AS artifact_namespace,
    all_addresses.address AS artifact_name,
    all_addresses.address AS artifact_id,
    'SOCIAL_HANDLE' AS artifact_type
  FROM all_addresses
  JOIN oso.stg_farcaster__profiles AS profiles
    ON all_addresses.farcaster_id = profiles.farcaster_id
)

SELECT DISTINCT
  @oso_entity_id(user_source, user_namespace, user_name) AS user_id,
  user_source_id,
  user_source,
  user_namespace,
  user_name,
  display_name,
  artifact_source,
  artifact_namespace,
  artifact_name,
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name) AS artifact_id,
  artifact_type
FROM artifacts_by_user
