MODEL (
  name oso.int_projects_by_collection_in_op_atlas,
  description "Many-to-many mapping of projects to Retro Funding round collections",
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

@DEF(collection_source, 'OP_ATLAS');
@DEF(collection_namespace, 'retro-funding');
@DEF(flagged_for_removal, [
  '0x8bfdc42f26bf691d378d2073ae509c46b85c0eed8db8abc6987b6725dd0d056a',
  '0x10da43868e7439419af2859f2539ed8b355a0f330bd05a6d028ddff8fd4a03d8'
]);

WITH measurement_periods AS (
  SELECT
    period_number,
    cutoff_date
  FROM (
    VALUES
      ('1', DATE '2025-03-11'),
      ('2', DATE '2025-04-11')
  ) AS t(period_number, cutoff_date)
),

app AS (
  SELECT DISTINCT
    project_id,
    project_name,
    round_id,
    created_at
  FROM oso.stg_op_atlas_application
  WHERE
    round_id IN ('7', '8')
    AND status = 'submitted'
    AND created_at >= DATE '2025-02-01'
    AND project_name NOT IN (
      SELECT project_name
      FROM UNNEST(@flagged_for_removal) AS t(project_name)
    )
),

projects_by_collection AS (
  SELECT DISTINCT
    @collection_source AS collection_source,
    @collection_namespace AS collection_namespace,
    CONCAT(app.round_id, '-', mp.period_number) AS collection_name,
    CASE
      WHEN app.round_id = '7'
      THEN 'Retro Funding S7: Developer Tooling'
      WHEN app.round_id = '8'
      THEN 'Retro Funding S7: Onchain Builders'
      ELSE NULL
    END AS collection_display_name,
    projects.project_source,
    projects.project_namespace,
    projects.project_name,
    app.project_id
  FROM app
  CROSS JOIN measurement_periods mp
  JOIN oso.stg_op_atlas_project AS projects
    ON app.project_id = projects.project_id
  WHERE app.created_at <= mp.cutoff_date
)
SELECT
  @oso_entity_id(collection_source, collection_namespace, collection_name)
    AS collection_id,
  collection_source,
  collection_namespace,
  collection_name,
  collection_display_name,
  project_id,
  project_source,
  project_namespace,
  project_name
FROM projects_by_collection