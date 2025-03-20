MODEL (
  name oso.int_superchain_s7_devtooling_onchain_builder_nodes,
  description "Identifies onchain builder nodes for the S7 devtooling round",
  dialect trino,
  kind full,
);

@DEF(gas_fees_threshold, 0.1);
@DEF(measurement_date, DATE('2025-03-01'));

/*
  Selects projects that meet the gas fees threshold and have been applied to the S7 devtooling round
  TODO: Need to pull the sample_date for future versions of this model
*/
WITH all_projects AS (
  SELECT
    project_id,
    transaction_count,
    gas_fees,
    active_addresses_count
  FROM oso.int_superchain_s7_onchain_builder_eligibility
  WHERE
    meets_all_criteria
    AND gas_fees >= @gas_fees_threshold
    AND sample_date = @measurement_date
),

ossd_projects AS (
  SELECT DISTINCT
    CASE WHEN ossd.ossd_project_id IS NOT NULL THEN ossd.ossd_project_id
         ELSE all_projects.project_id
    END AS project_id,
    all_projects.transaction_count,
    all_projects.gas_fees,
    all_projects.active_addresses_count
  FROM all_projects
  LEFT OUTER JOIN oso.int_projects_to_projects AS ossd
    ON all_projects.project_id = ossd.ossd_project_id
)

SELECT
  @measurement_date AS sample_date,
  ossd_projects.project_id,
  p.project_name,
  p.display_name,
  ossd_projects.transaction_count,
  ossd_projects.gas_fees,
  ossd_projects.active_addresses_count
FROM ossd_projects
JOIN oso.projects_v1 AS p
  ON ossd_projects.project_id = p.project_id