MODEL (
  name oso.int_addresses_by_ens_user,
  kind FULL,
  description "EVM addresses linked to ENS domains",
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH owner_addresses AS (
  SELECT DISTINCT
    name,
    owner.id AS address
  FROM oso.stg_ens__domains
  WHERE
    owner.id IS NOT NULL
    AND LENGTH(owner.id) = 42
    AND owner.id LIKE '0x%'
),

artifacts_by_user AS (
  SELECT
    owner_addresses.name AS user_source_id,
    'ENS' AS user_source,
    '' AS user_namespace,
    owner_addresses.name AS user_name,
    owner_addresses.name AS display_name,
    'MAINNET' AS artifact_source,
    '' AS artifact_namespace,
    owner_addresses.address AS artifact_name,
    owner_addresses.address AS artifact_id,
    'SOCIAL_HANDLE' AS artifact_type
  FROM owner_addresses
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
