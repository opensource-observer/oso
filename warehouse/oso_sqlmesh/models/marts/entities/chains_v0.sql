MODEL (
  name oso.chains_v0,
  kind FULL,
  tags (
    'export'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  description 'The `chains_v0` table contains a mapping of chain names to their OSO-maintained name, Chainlist-maintained ID, and display name. This table is intended to help with chain-related data normalization.',
  column_descriptions (
    chain_name = 'The OSO-maintained name for the chain, used as the artifact source for blockchain addresses and the event source for blockchain events.',
    chain_id = 'The Chainlist-maintained ID for the chain.',
    display_name = 'The display name for the chain used in the UI.'
  )
);

SELECT DISTINCT
  oso_chain_name::VARCHAR AS chain_name,
  chain_id::INTEGER AS chain_id,
  display_name::VARCHAR AS display_name
FROM oso.int_chainlist
ORDER BY chain_name ASC