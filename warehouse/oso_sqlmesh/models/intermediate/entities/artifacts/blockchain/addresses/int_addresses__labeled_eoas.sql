MODEL(
  name oso.int_addresses__labeled_eoas,
  description 'Addresses labeled as EOAs by OLI or other sources',
  kind full,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH oli_eoas AS (
  SELECT DISTINCT address
  FROM oso.int_addresses__openlabelsinitiative
  WHERE address_type = 'EOA'
),

bridges AS (
  SELECT DISTINCT address
  FROM oso.seed_known_eoa_bridges
),

unioned AS (
  SELECT * FROM oli_eoas
  UNION ALL
  SELECT * FROM bridges
)

SELECT DISTINCT
  LOWER(unioned.address) AS address,
  UPPER(chains.chain_name) AS chain
FROM unioned
CROSS JOIN oso.seed_chain_id_to_chain_name AS chains