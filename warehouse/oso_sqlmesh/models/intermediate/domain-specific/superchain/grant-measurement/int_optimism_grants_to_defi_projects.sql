MODEL (
  name oso.int_optimism_grants_to_defi_projects,
  description 'Optimism grants to DeFi projects',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  ),
  tags (
    'entity_category=project'
  )
);


WITH projects_with_defi_category AS (
  SELECT
    g.oso_project_id,
    dl.category
  FROM oso.int_optimism_grants AS g
  JOIN oso.int_artifacts_by_project_in_ossd AS abp
    ON abp.project_id = g.oso_project_id
    AND abp.artifact_type = 'DEFILLAMA_PROTOCOL'
  JOIN oso.int_artifacts_by_project_in_defillama AS dl
    ON abp.artifact_id = dl.artifact_id
),
refined_categories AS (
  SELECT
    oso_project_id,
    CASE
      WHEN category IN ('bridge', 'lending', 'dexs') THEN category
      WHEN category IN ('yield', 'yield_aggregator') THEN 'yield'
      WHEN category IN ('synthetics', 'derivatives', 'options')
        THEN 'derivatives'
      ELSE 'other'
    END AS vertical
  FROM projects_with_defi_category
),
grouped_verticals AS (
  SELECT
    oso_project_id,
    array_agg(DISTINCT vertical) AS verts,
    array_sort(array_agg(DISTINCT vertical)) AS all_verticals
  FROM refined_categories
  GROUP BY 1
),
vertical_tags AS (
  SELECT
    oso_project_id,
    CASE
      WHEN cardinality(verts)=1 THEN verts[1]
      WHEN
        cardinality(filter(verts, x -> x <> 'other'))=1
        THEN (filter(verts, x -> x <> 'other'))[1]
      ELSE 'multiple'
    END AS best_vertical,
    all_verticals
  FROM grouped_verticals
)

SELECT
  g.oso_project_id,
  g.oso_project_name,
  g.oso_project_display_name,
  vt.best_vertical,
  vt.all_verticals
FROM oso.int_optimism_grants AS g
JOIN vertical_tags AS vt
  ON g.oso_project_id = vt.oso_project_id