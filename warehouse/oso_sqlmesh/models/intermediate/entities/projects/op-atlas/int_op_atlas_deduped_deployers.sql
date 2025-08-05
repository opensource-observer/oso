MODEL (
  name oso.int_op_atlas_deduped_deployers,
  description "Deduplicates deployers in OP Atlas",
  kind FULL,
  dialect trino,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH all_deployers AS (
  SELECT
    op_atlas_project.display_name,
    pc.atlas_id,
    pc.deployer_address,
    pc.contract_address,
    pc.chain_id,
    op_atlas_project.created_at AS project_created_at,
    app.created_at AS application_created_at,
    app.round_id AS application_round_id,
    COUNT(DISTINCT pc.atlas_id) OVER (PARTITION BY pc.deployer_address, pc.chain_id) AS project_count_for_deployer
  FROM oso.stg_op_atlas_project_contract AS pc
  JOIN oso.stg_op_atlas_project AS op_atlas_project
    ON op_atlas_project.atlas_id = pc.atlas_id
  LEFT JOIN oso.stg_op_atlas_application AS app
    ON app.atlas_id = pc.atlas_id
    AND app.status = 'submitted'
),

-- Single project gets the deployer
single_project_deployers AS (
  SELECT
    display_name,
    atlas_id,
    deployer_address,
    contract_address,
    chain_id,
    project_created_at,
    application_created_at,
    application_round_id,
    'SINGLE_PROJECT' AS assignment_reason
  FROM all_deployers
  WHERE project_count_for_deployer = 1
),

-- Multiple projects - prioritize by application or project creation date
multi_project_deployers AS (
  SELECT
    display_name,
    atlas_id,
    deployer_address,
    contract_address,
    chain_id,
    project_created_at,
    application_created_at,
    application_round_id,
    CASE 
      WHEN application_created_at IS NOT NULL THEN 'EARLIEST_APP_FOR_GREATEST_ROUND'
      ELSE 'EARLIEST_PROJECT_CREATION'
    END AS assignment_reason,
    ROW_NUMBER() OVER (
      PARTITION BY deployer_address, chain_id
      ORDER BY 
        -- First prioritize by greatest round_id (descending)
        COALESCE(CAST(application_round_id AS INTEGER), 0) DESC,
        -- Then by earliest project created_at (ascending)
        COALESCE(project_created_at, DATE('9999-12-31')) ASC
    ) AS deployer_rank
  FROM all_deployers
  WHERE project_count_for_deployer > 1
)

SELECT
  display_name,
  atlas_id,
  deployer_address,
  contract_address,
  chain_id,
  project_created_at,
  application_created_at,
  application_round_id,
  assignment_reason
FROM single_project_deployers

UNION ALL

SELECT
  display_name,
  atlas_id,
  deployer_address,
  contract_address,
  chain_id,
  project_created_at,
  application_created_at,
  application_round_id,
  assignment_reason
FROM multi_project_deployers
WHERE deployer_rank = 1