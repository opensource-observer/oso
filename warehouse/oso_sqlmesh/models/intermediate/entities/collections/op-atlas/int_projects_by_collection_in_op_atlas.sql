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
  '0x8bfdc42f26bf691d378d2073ae509c46b85c0eed8db8abc6987b6725dd0d056a', -- Spam
  '0x10da43868e7439419af2859f2539ed8b355a0f330bd05a6d028ddff8fd4a03d8', -- Spam
  '0x51504348243d8e8fa59cf2ba983d9255373e5eb23fe22a0d18c0d36028561ace', -- Test
  '0xaa1b878800206da24ee7297fb202ef98a6af0fb3ec298a65ba6b675cb4f4144b', -- Test
  '0xcbfdcf8f724d73504d1518d5ecd7d7256b12d37e68cd84569b383bfb6e2eeea4'  -- Dmail
]);

WITH measurement_periods AS (
  SELECT
    period_number,
    cutoff_date
  FROM (
    VALUES
      ('1', DATE '2025-03-11'),
      ('2', DATE '2025-04-11'),
      ('3', DATE '2025-05-11'),
      ('4', DATE '2025-06-05'),
      ('5', DATE '2025-07-08'),
      ('6', DATE '2025-08-01')
  ) AS t(period_number, cutoff_date)
),

app AS (
  SELECT DISTINCT
    atlas_id,
    round_id,
    created_at
  FROM oso.stg_op_atlas_application
  WHERE
    round_id IN ('7', '8')
    AND status = 'submitted'
    AND created_at >= DATE '2025-02-01'
    AND atlas_id NOT IN (
      SELECT atlas_id
      FROM UNNEST(@flagged_for_removal) AS t(atlas_id)
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
    'OP_ATLAS' AS project_source,
    '' AS project_namespace,
    projects.atlas_id AS project_name
  FROM app
  CROSS JOIN measurement_periods AS mp
  JOIN oso.stg_op_atlas_project AS projects
    ON app.atlas_id = projects.atlas_id
  WHERE app.created_at <= mp.cutoff_date
)
SELECT
  @oso_entity_id(collection_source, collection_namespace, collection_name)
    AS collection_id,
  collection_source,
  collection_namespace,
  collection_name,
  collection_display_name,
  @oso_entity_id(project_source, project_namespace, project_name)
    AS project_id,
  project_source,
  project_namespace,
  project_name
FROM projects_by_collection
