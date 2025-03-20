MODEL(
  name oso.int_defillama_protocol_mapping,
  description 'Defillama protocol-to-parent protocol mapping',
  kind full
);

SELECT DISTINCT
  parent_protocol,
  CONCAT('https://defillama.com/protocol/', protocol) AS artifact_source_id,
  'DEFILLAMA' AS artifact_source,
  '' AS artifact_namespace,
  protocol AS artifact_name,
  CONCAT('https://defillama.com/protocol/', protocol) AS artifact_url,
  'DEFILLAMA_PROTOCOL' AS artifact_type
FROM oso.stg__defillama_tvl_events
WHERE parent_protocol IS NOT NULL