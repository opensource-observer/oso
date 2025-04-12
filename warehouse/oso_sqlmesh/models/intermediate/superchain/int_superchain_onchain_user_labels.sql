-- TODO: Currently only includes farcaster users.

MODEL(
  name oso.int_superchain_onchain_user_labels,
  description 'Onchain user labels',
  kind full,
  audits (
    number_of_rows(threshold := 0)
  )
);


WITH farcaster_addresses AS (
  SELECT
    artifacts.user_id,
    artifacts.farcaster_id,
    artifacts.address,
    chain_names.chain
  FROM oso.int_artifacts_by_farcaster_user AS artifacts
  CROSS JOIN oso.int_superchain_chain_names AS chain_names
)

SELECT
  user_id,
  farcaster_id,
  chain AS artifact_source,
  @oso_entity_id(chain, '', address) AS artifact_id,
  '' AS artifact_namespace,
  address AS artifact_name,
  true AS is_farcaster_user
FROM farcaster_addresses
