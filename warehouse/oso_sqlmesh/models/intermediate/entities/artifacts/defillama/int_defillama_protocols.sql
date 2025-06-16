MODEL(
  name oso.int_defillama_protocols,
  description 'Defillama protocols',
  kind FULL,
  dialect trino,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT DISTINCT
  slug AS protocol,
  CASE 
    WHEN parent_protocol LIKE 'parent#%' THEN SPLIT(parent_protocol, '#')[2]
    ELSE NULL
  END AS parent_protocol,
  CONCAT('https://defillama.com/protocol/', slug) AS url
FROM oso.stg_defillama__protocol_metadata