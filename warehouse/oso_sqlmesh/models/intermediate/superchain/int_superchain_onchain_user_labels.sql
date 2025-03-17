-- TODO: Currently only includes farcaster users.

MODEL(
  name oso.int_superchain_onchain_user_labels,
  description 'Onchain user labels',
  kind full
);

@DEF(chains, [
  'base',
  'bob',
  'frax',
  'ink',
  'kroma',
  'lisk',
  'lyra',
  'metal',
  'mint',
  'mode',
  'optimism',
  'orderly',
  'polynomial',
  'race',
  'redstone',
  'scroll',
  'shape',
  'soneium',
  'swan',
  'swell',
  'unichain',
  'worldchain',
  'xterio',
  'zora'
]);

WITH chains_struct AS (
  SELECT UPPER(t.chain) as chain
  FROM UNNEST(@chains) AS t(chain)
),

farcaster_addresses AS (
  SELECT
    artifacts.user_id,
    artifacts.farcaster_id,
    artifacts.address,
    chains_struct.chain
  FROM oso.int_artifacts_by_farcaster_user AS artifacts
  CROSS JOIN chains_struct
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
