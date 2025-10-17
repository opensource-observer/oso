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


WITH grantees AS (
  SELECT DISTINCT
    oso_project_id,
    oso_project_name,
    oso_project_display_name,
  FROM oso.int_optimism_grants
),
projects_with_defi_category AS (
  SELECT
    g.oso_project_id,
    dl.category
  FROM grantees AS g
  JOIN oso.int_artifacts_by_project_in_ossd AS abp
    ON abp.project_id = g.oso_project_id
    AND abp.artifact_type = 'DEFILLAMA_PROTOCOL'
  JOIN oso.int_artifacts_by_project_in_defillama AS dl
    ON abp.artifact_id = dl.artifact_id
),
refined_categories AS (
  SELECT
    oso_project_id,
    category,
    CASE
      WHEN category IN ('Dexs', 'Lending', 'Liquid Staking') THEN category
      WHEN category IN ('Cross Chain Bridge', 'Bridge') THEN 'Bridge'
      WHEN category IN ('Yield', 'Yield Aggregator') THEN 'Yield'
      WHEN category IN ('Synthetics', 'Derivatives', 'Options')
        THEN 'Derivatives'
      ELSE 'Other'
    END AS vertical
  FROM projects_with_defi_category
),
grouped_verticals AS (
  SELECT
    oso_project_id,
    array_sort(array_agg(DISTINCT vertical)) AS all_verticals,
    array_sort(array_agg(DISTINCT category)) AS all_categories
  FROM refined_categories
  GROUP BY 1
),
vertical_tags AS (
  SELECT
    oso_project_id,
    CASE
      WHEN cardinality(all_verticals)=1 THEN all_verticals[1]
      WHEN
        cardinality(filter(all_verticals, x -> x <> 'Other'))=1
        THEN (filter(all_verticals, x -> x <> 'Other'))[1]
      ELSE 'Multiple'
    END AS best_vertical,
    all_verticals,
    all_categories
  FROM grouped_verticals
)

SELECT
  g.oso_project_id,
  g.oso_project_name,
  g.oso_project_display_name,
  vt.best_vertical,
  vt.all_verticals,
  vt.all_categories
FROM grantees AS g
JOIN vertical_tags AS vt
  ON g.oso_project_id = vt.oso_project_id