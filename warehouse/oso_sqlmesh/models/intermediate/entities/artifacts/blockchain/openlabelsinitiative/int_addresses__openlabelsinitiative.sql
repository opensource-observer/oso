MODEL(
  name oso.int_addresses__openlabelsinitiative,
  description 'Normalized addresses from the Open Labels Initiative',
  dialect trino,
  kind full,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH pivoted AS (
  SELECT
    CASE WHEN tag_id = 'deployer_address' THEN tag_value ELSE address END
      AS address,
    CASE 
  WHEN regexp_like(SPLIT_PART(chain_id, ':', 2), '^\d+$') 
    THEN CAST(SPLIT_PART(chain_id, ':', 2) AS INTEGER)
  ELSE NULL
END AS chain_id,
    MAX(CASE WHEN tag_id = 'owner_project' THEN tag_value ELSE NULL END)
      AS owner_project,
    FLATTEN(ARRAY_AGG(
      CASE
        WHEN tag_id = 'is_eoa' THEN ['EOA']
        WHEN tag_id = 'is_proxy' THEN ['CONTRACT', 'PROXY']
        WHEN tag_id = 'is_factory_contract' THEN ['FACTORY', 'CONTRACT']
        WHEN tag_id = 'is_paymaster' THEN ['PAYMASTER']
        WHEN tag_id = 'is_safe_contract' THEN ['SAFE']
        WHEN tag_id = 'deployer_address' THEN ['DEPLOYER']
        WHEN tag_id = 'erc_type' THEN [UPPER(tag_value)]
        ELSE []
      END
    )) AS address_types
  FROM oso.stg_openlabelsinitiative__labels_decoded AS labels
  GROUP BY 1,2
),

normalized AS (
  SELECT DISTINCT
    p.address,
    p.chain_id,
    p.owner_project,
    unnested.address_type
  FROM pivoted AS p
  CROSS JOIN UNNEST(p.address_types) AS unnested(address_type)
)

SELECT
  n.address,
  n.chain_id,
  cl.oso_chain_name AS chain,
  n.owner_project,
  n.address_type
FROM normalized AS n
JOIN oso.int_chainlist AS cl
  ON n.chain_id = cl.chain_id
