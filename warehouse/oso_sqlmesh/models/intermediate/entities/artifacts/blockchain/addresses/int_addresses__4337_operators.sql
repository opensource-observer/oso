MODEL(
  name oso.int_addresses__4337_operators,
  description '4337 address labels from the Open Labels Initiative',
  kind full,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH all_4337_addresses AS (
  SELECT DISTINCT address
  FROM oso.stg_openlabelsinitiative__labels_decoded
  WHERE tag_value LIKE '%4337%'
)

SELECT DISTINCT
  address,
  chain,
  owner_project
FROM oso.int_addresses__openlabelsinitiative
WHERE address IN (SELECT address FROM all_4337_addresses)
