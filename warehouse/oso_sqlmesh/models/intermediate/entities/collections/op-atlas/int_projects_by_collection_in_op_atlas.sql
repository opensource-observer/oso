MODEL (
  name oso.int_projects_by_collection_in_op_atlas,
  description "Many-to-many mapping of projects to Retro Funding round collections. Note: this model gets updated once per month to reflect the latest Retro Funding round cutoff dates.",
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

@DEF(collection_source, 'OP_ATLAS');
@DEF(project_source, 'OP_ATLAS');
@DEF(collection_namespace, 'retro-funding');
@DEF(project_namespace, '');
@DEF(app_submitted_after, DATE '2025-02-01');
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
    cutoff_date,
    CASE WHEN period_number BETWEEN 1 AND 6 THEN 'S7' ELSE 'S8' END AS season
  FROM (VALUES
    (1, DATE '2025-03-11'),
    (2, DATE '2025-04-11'),
    (3, DATE '2025-05-11'),
    (4, DATE '2025-06-05'),
    (5, DATE '2025-07-08'),
    (6, DATE '2025-08-01'),
    (7, DATE '2025-09-01')
  ) AS t(period_number, cutoff_date)
),

round_labels AS (
  SELECT * FROM (VALUES
    (7, 'Developer Tooling'),
    (8, 'Onchain Builders')
  ) AS t(round_id,label)
),

flagged AS (
  SELECT atlas_id
  FROM UNNEST(@flagged_for_removal) AS t(atlas_id)
),

apps AS (
  SELECT
    a.atlas_id,
    p.display_name,
    CAST(a.round_id AS INTEGER) AS round_id,
    CAST(a.created_at AS DATE) AS application_date
  FROM oso.stg_op_atlas_application AS a
  JOIN oso.stg_op_atlas_project AS p
    ON a.atlas_id=p.atlas_id
  WHERE a.status = 'submitted'
),

filtered_apps AS (
  SELECT a.*
  FROM apps AS a
  WHERE a.round_id IN (7,8)
    AND a.application_date >= @app_submitted_after
    AND NOT EXISTS (
      SELECT 1 FROM flagged f WHERE f.atlas_id = a.atlas_id
    )
),

projects_by_collection AS (
  SELECT
    @collection_source AS collection_source,
    @collection_namespace AS collection_namespace,
    CAST(a.round_id AS VARCHAR) || '-' || CAST(mp.period_number AS VARCHAR)
      AS collection_name,
    'Retro Funding ' || mp.season || ': ' || rl.label
      AS collection_display_name,
    mp.period_number,
    mp.cutoff_date,
    mp.season,
    @project_source AS project_source,
    @project_namespace AS project_namespace,
    a.atlas_id AS project_name,
    a.display_name AS project_display_name,
    a.application_date
  FROM filtered_apps AS a
  JOIN round_labels AS rl
    ON rl.round_id = a.round_id
  CROSS JOIN measurement_periods AS mp
  WHERE a.application_date <= mp.cutoff_date
)

SELECT DISTINCT
  @oso_entity_id(collection_source,collection_namespace,collection_name) AS collection_id,
  collection_source,
  collection_namespace,
  collection_name,
  collection_display_name,
  period_number,
  cutoff_date,
  season,
  @oso_entity_id(project_source,project_namespace,project_name) AS project_id,
  project_source,
  project_namespace,
  project_name,
  project_display_name,
  application_date
FROM projects_by_collection