MODEL (
  name oso.int_projects_by_collection_in_op_atlas,
  description "Many-to-many mapping of projects to Retro Funding round collections",
  kind FULL
);

@DEF(collection_source, 'OP_ATLAS');
@DEF(collection_namespace, 'retro-funding');

WITH app AS (
  SELECT DISTINCT
    project_id,
    project_name,
    round_id
  FROM oso.stg_op_atlas_application
  WHERE
    round_id IN ('7', '8')
    AND status = 'submitted'
    AND created_at BETWEEN DATE '2025-02-01' AND DATE '2025-03-10'
),

projects_by_collection AS (
  SELECT DISTINCT
    @collection_source AS collection_source,
    @collection_namespace AS collection_namespace,
    CONCAT(app.round_id, '-', '1') AS collection_name,
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
  JOIN oso.stg_op_atlas_project AS projects
    ON app.project_id = projects.project_id
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