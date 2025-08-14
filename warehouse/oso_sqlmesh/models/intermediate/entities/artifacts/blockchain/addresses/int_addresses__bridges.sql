MODEL (
  name oso.int_addresses__bridges,
  kind FULL,
  dialect trino,
  description "Cross-chain EOA bridges",
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);


SELECT DISTINCT
  LOWER(bridges.address) AS address,
  UPPER(chains.chain_name) AS chain
FROM oso.seed_known_eoa_bridges AS bridges
CROSS JOIN oso.seed_chain_id_to_chain_name AS chains