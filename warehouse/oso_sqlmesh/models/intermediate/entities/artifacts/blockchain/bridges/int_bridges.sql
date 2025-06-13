MODEL (
  name oso.int_bridges,
  kind FULL,
  dialect trino,
  grain (bridge_address, chain),
  description "All known EOA-based EVM bridges",
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  eoas.bridge_address AS bridge_address,
  chains.chain AS chain
FROM oso.seed_known_bridge_eoas AS eoas
CROSS JOIN oso.seed_chainlist AS chains