MODEL (
  name oso.int_superchain_s7_defillama_adapter_checks,
  description 'Defillama adapter checks',
  kind VIEW,
  dialect trino,
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);

@DEF(sample_date, '2025-06-01');

WITH project_data AS (
  SELECT
    p.project_id,
    p.project_name,
    p.display_name,
    atlas.artifact_name,
    m.amount
  FROM oso.int_artifacts_by_project_in_op_atlas AS atlas
  JOIN oso.projects_v1 AS p
    ON atlas.project_id = p.project_id
  JOIN oso.int_superchain_s7_onchain_metrics_by_project AS m
    ON p.project_id = m.project_id
  JOIN oso.projects_by_collection_v1 AS pc
    ON m.project_id = pc.project_id
  WHERE
    atlas.artifact_source = 'DEFILLAMA'
    AND m.metric_name = 'average_tvl_monthly'
    AND m.sample_date = DATE(@sample_date)
    AND m.amount > 0
),

tvl_agg AS (
  SELECT
    project_id,
    SUM(amount) AS total_tvl
  FROM project_data
  GROUP BY project_id
),

adapters_agg AS (
  SELECT
    project_id,
    array_agg(DISTINCT artifact_name ORDER BY artifact_name) AS defillama_adapters
  FROM project_data
  GROUP BY project_id
),

adapter_counts AS (
  SELECT
    artifact_name,
    COUNT(DISTINCT project_id) AS project_count
  FROM project_data
  GROUP BY artifact_name
),

shared_flags AS (
  SELECT
    aa.project_id,
    MAX(CASE WHEN ac.project_count > 1 THEN TRUE ELSE FALSE END) AS has_shared_adapter
  FROM adapters_agg AS aa
  CROSS JOIN UNNEST(aa.defillama_adapters) AS t(adapter)
  JOIN adapter_counts AS ac
    ON t.adapter = ac.artifact_name
  GROUP BY aa.project_id
)

SELECT
  pd.project_name,
  pd.display_name,
  ta.total_tvl,
  aa.defillama_adapters,
  sf.has_shared_adapter
FROM tvl_agg AS ta
JOIN adapters_agg AS aa
  ON ta.project_id = aa.project_id
JOIN shared_flags AS sf
  ON ta.project_id = sf.project_id
JOIN oso.projects_v1 AS pd
  ON ta.project_id = pd.project_id
ORDER BY ta.total_tvl DESC