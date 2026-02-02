MODEL(
  name oso.int_addresses__openlabelsinitiative,
  description 'Normalized addresses from the Open Labels Initiative',
  dialect trino,
  kind full,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH filtered_addresses AS (
  SELECT DISTINCT
    address,
    tag_id,
    tag_value,
    SPLIT_PART(chain_id, ':', 2) AS chain_id_str
  FROM oso.stg_openlabelsinitiative__labels_decoded
  WHERE
    chain_id LIKE '%:%'
    AND tag_id IN (
      'owner_project', 'usage_category',
      'is_eoa', 'is_proxy', 'is_factory_contract', 
      'is_paymaster', 'is_safe_contract',
      'deployer_address', 'erc_type'
    )
),

WITH filtered_addresses AS (
  SELECT DISTINCT
    address,
    tag_id,
    tag_value,
    SPLIT_PART(chain_id, ':', 2) AS chain_id_str
  FROM oso.stg_openlabelsinitiative__labels_decoded
  WHERE
    chain_id LIKE '%:%'
    AND tag_id IN (
      'owner_project', 'usage_category',
      'is_eoa', 'is_proxy', 'is_factory_contract', 
      'is_paymaster', 'is_safe_contract',
      'deployer_address', 'erc_type'
    )
),

pivoted AS (
  SELECT
    CASE WHEN tag_id = 'deployer_address' THEN tag_value ELSE address END
      AS address,
    TRY_CAST(
      CASE
        WHEN chain_id_str LIKE 'any' THEN 1
        ELSE TRY_CAST(chain_id_str AS BIGINT)
      END AS BIGINT
    ) AS chain_id,
    MAX(CASE WHEN tag_id = 'owner_project' THEN tag_value ELSE NULL END)
      AS owner_project,
    MAX(CASE WHEN tag_id = 'usage_category' THEN tag_value ELSE NULL END)
      AS usage_category,
    FLATTEN(ARRAY_AGG(
      CASE
        WHEN tag_id = 'is_eoa' THEN ['EOA']
        WHEN tag_id = 'is_proxy' THEN ['CONTRACT', 'PROXY']
        WHEN tag_id = 'is_factory_contract' THEN ['FACTORY', 'CONTRACT']
        WHEN tag_id = 'is_paymaster' THEN ['PAYMASTER']
        WHEN tag_id = 'is_safe_contract' THEN ['SAFE']
        WHEN tag_id = 'deployer_address' THEN ['DEPLOYER']
        WHEN tag_id = 'erc_type' AND tag_value = '["erc20"]' THEN ['TOKEN']
        ELSE []
      END
    )) AS address_types
  FROM filtered_addresses
  GROUP BY 1,2
),

normalized AS (
  SELECT DISTINCT
    p.address,
    p.chain_id,
    p.owner_project,
    p.usage_category,
    unnested.address_type
  FROM pivoted AS p
  CROSS JOIN UNNEST(p.address_types) AS unnested(address_type)
)

SELECT
  n.address,
  n.chain_id,
  cl.oso_chain_name AS chain,
  n.owner_project,
  n.usage_category,
  n.address_type
FROM normalized AS n
JOIN oso.int_chainlist AS cl
  ON n.chain_id = cl.chain_id