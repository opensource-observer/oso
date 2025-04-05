MODEL (
  name oso.int_superchain_s7_m1_rewards,
  description 'Rewards for Retro Funding S7 - Measurement Period 1 (Feb 2025)',
  dialect trino,
  kind full,
  grain (project_id, chain, sample_date),
);

@DEF(measurement_date, DATE('2025-02-28'));

WITH results AS (
  SELECT 
    atlas_id,
    amount,
    round_id
  FROM oso.seed_optimism_s7_m1_rewards
),

joined_results AS (
  SELECT
    projects.project_id,
    results.atlas_id as project_name,
    CASE
      WHEN results.round_id = 7 THEN 'S7_M1_devtooling_reward'
      WHEN results.round_id = 8 THEN 'S7_M1_onchain_builder_reward'
      ELSE null
    END AS metric,
    results.amount
  FROM results
  JOIN oso.projects_v1 AS projects
    ON results.atlas_id = projects.project_name
)

SELECT
  @measurement_date::DATE AS sample_date,
  project_id::TEXT,
  project_name::TEXT,
  metric::TEXT,
  amount::DOUBLE
FROM joined_results
WHERE metric IS NOT NULL