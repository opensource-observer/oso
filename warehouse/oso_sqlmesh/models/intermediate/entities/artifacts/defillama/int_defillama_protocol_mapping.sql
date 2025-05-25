MODEL(
  name oso.int_defillama_protocol_mapping,
  description 'Defillama protocol-to-parent protocol mapping',
  kind full,
  dialect trino,
  audits (
    not_null(columns := (parent_protocol, artifact_name))
  )
);

WITH parent_protocols AS (  
  SELECT DISTINCT
    protocol,
    CASE 
      WHEN parent_protocol LIKE '%#%' THEN SPLIT(parent_protocol, '#')[2]
      ELSE parent_protocol 
    END AS parent_protocol
  FROM oso.stg_defillama__tvl_events
  WHERE
    parent_protocol IS NOT NULL
    AND parent_protocol != ''
)

SELECT DISTINCT
  parent_protocol,
  CONCAT('https://defillama.com/protocol/', protocol) AS artifact_source_id,
  'DEFILLAMA' AS artifact_source,
  '' AS artifact_namespace,
  protocol AS artifact_name,
  CONCAT('https://defillama.com/protocol/', protocol) AS artifact_url,
  'DEFILLAMA_PROTOCOL' AS artifact_type
FROM parent_protocols