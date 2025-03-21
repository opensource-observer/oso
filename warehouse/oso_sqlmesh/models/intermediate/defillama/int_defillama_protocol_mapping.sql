MODEL(
  name oso.int_defillama_protocol_mapping,
  description 'Defillama protocol-to-parent protocol mapping',
  kind full
);

WITH manual_mappings AS (
  SELECT
    parent_protocol,
    protocol
  FROM (VALUES
    ('uniswap', 'uniswap-v3'),
    ('uniswap', 'uniswap-v2'),
    ('bmx', 'bmx-classic-perps'),
    ('bmx', 'bmx-freestyle')
  ) AS mappings (parent_protocol, protocol)
),

stg_defillama_protocols AS (
  SELECT DISTINCT
    parent_protocol,
    protocol
  FROM oso.stg__defillama_tvl_events
  WHERE parent_protocol IS NOT NULL
),

unioned_protocols AS (
  SELECT * FROM manual_mappings
  UNION
  SELECT * FROM stg_defillama_protocols
)

SELECT DISTINCT
  parent_protocol,
  CONCAT('https://defillama.com/protocol/', protocol) AS artifact_source_id,
  'DEFILLAMA' AS artifact_source,
  '' AS artifact_namespace,
  protocol AS artifact_name,
  CONCAT('https://defillama.com/protocol/', protocol) AS artifact_url,
  'DEFILLAMA_PROTOCOL' AS artifact_type
FROM unioned_protocols