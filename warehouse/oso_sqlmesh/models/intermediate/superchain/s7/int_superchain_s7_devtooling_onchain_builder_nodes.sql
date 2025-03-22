/*
  This model identifies onchain builder nodes for the S7 devtooling round.
  It does this by:
  1. Selecting all projects that meet the gas fees threshold
  2. Mapping OP Atlas projects to their OSS Directory project IDs
  3. Carrying forward the project name and source, and mapping the project ID
     to the OSS Directory project ID if it exists.

  TODO: Need to pull the sample_date for future versions of this model
*/

MODEL (
  name oso.int_superchain_s7_devtooling_onchain_builder_nodes,
  description "Identifies onchain builder nodes for the S7 devtooling round",
  dialect trino,
  kind full,
);

@DEF(gas_fees_threshold, 0.1);
@DEF(measurement_date, DATE('2025-03-01'));

/*
  Step 1: Select all projects that meet the gas fees threshold
  (regardless of whether they've been applied to the S7 devtooling round)
*/
WITH all_projects AS (
  SELECT
    e.project_id,
    p.project_name,
    p.display_name,
    p.project_source,
    e.transaction_count,
    e.gas_fees,
    e.active_addresses_count
  FROM oso.int_superchain_s7_onchain_builder_eligibility AS e
  JOIN oso.projects_v1 AS p
    ON e.project_id = p.project_id
  WHERE
    e.meets_all_criteria
    AND e.gas_fees >= @gas_fees_threshold
    AND e.sample_date = @measurement_date
),

/*
  Step 2: Map OP Atlas projects to their OSS Directory project IDs
  using GitHub as the intermediate source. This is because projects
  usually apply to the Onchain Builder program with just their contracts
  repo, not their entire project.
*/
p2p AS (
  SELECT
    ossd_project_id,
    external_project_name AS op_atlas_project_name
  FROM oso.int_projects_to_projects
  WHERE
    external_project_source = 'OP_ATLAS'
    AND artifact_id IN (SELECT artifact_id FROM oso.repositories_v0)
)

/*
  Step 3: Carry forward the project name and source, and map the project ID
  to the OSS Directory project ID if it exists. Note: this may result in some
  projects appearing multiple times in the output, but this is fine because in
  the next step we'll filter for distinct GitHub artifacts only.
*/
SELECT DISTINCT
  @measurement_date AS sample_date,
  all_projects.project_id,
  all_projects.display_name,
  CASE
    WHEN all_projects.project_source = 'OP_ATLAS' THEN all_projects.project_name
    ELSE p2p.op_atlas_project_name
  END AS op_atlas_project_name,
  all_projects.project_source,
  all_projects.transaction_count,
  all_projects.gas_fees,
  all_projects.active_addresses_count
FROM all_projects
LEFT JOIN p2p
  ON all_projects.project_id = p2p.ossd_project_id