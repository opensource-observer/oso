/* TODO: turn this into a rolling model that includes a sample date (eg, every week) */
MODEL (
  name oso.int_superchain_s7_onchain_builder_eligibility,
  description "Determines if a project is eligible for measurement in the S7 onchain builder round",
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column sample_date,
    batch_size 90,
    batch_concurrency 1,
    lookback 7
  ),
  start @blockchain_incremental_start,
  cron '@daily',
  partitioned_by DAY("sample_date"),
  grain (sample_date, project_id)
);

@DEF(measurement_date, DATE('2025-02-28'));
@DEF(lookback_days, 180);
@DEF(transactions_threshold, 1000);
@DEF(gas_fees_threshold, 0.0);
@DEF(active_addresses_threshold, 420);
@DEF(days_with_onchain_activity_threshold, 10);

WITH all_projects AS (
  SELECT
    project_id,
    MAX(
      CASE WHEN collection_name = '8-1' THEN true ELSE false END
    ) as applied_to_round
  FROM oso.projects_by_collection_v1
  GROUP BY 1
),

events AS (
  SELECT *
  FROM oso.int_superchain_events_by_project
  WHERE    
    "time" BETWEEN @measurement_date - INTERVAL @lookback_days DAY
      AND @measurement_date
    AND event_type IN ('CONTRACT_INVOCATION', 'CONTRACT_INTERNAL_INVOCATION')
),

builder_metrics AS (
  SELECT
    all_projects.project_id,
    all_projects.applied_to_round,
    COUNT(DISTINCT events.transaction_hash) AS transaction_count,
    COUNT(DISTINCT events.from_artifact_id) AS active_addresses_count,
    COUNT(DISTINCT DATE_TRUNC('DAY', events.time)) AS active_days,
    SUM(events.gas_fee::DOUBLE) AS gas_fees
  FROM all_projects
  LEFT OUTER JOIN events
    ON all_projects.project_id = events.project_id
  GROUP BY
    all_projects.project_id,
    all_projects.applied_to_round
),

project_eligibility AS (
  SELECT
    project_id,
    (
      CAST(transaction_count >= @transactions_threshold AS INTEGER) +
      CAST(active_days >= @days_with_onchain_activity_threshold AS INTEGER) +
      CAST(active_addresses_count >= @active_addresses_threshold AS INTEGER) +
      CAST(gas_fees >= @gas_fees_threshold AS INTEGER)
      >= 3
    ) AS meets_all_criteria
  FROM builder_metrics
),

artifacts AS (
  SELECT DISTINCT
    project_id,
    'DEFILLAMA_ADAPTER' AS artifact_type
  FROM oso.artifacts_by_project_v1
  WHERE artifact_source = 'DEFILLAMA'

  UNION ALL

  SELECT DISTINCT
    p2p.external_project_id AS project_id,
    'BUNDLE_BEAR' AS artifact_type
  FROM oso.int_projects_to_projects AS p2p
  JOIN oso.artifacts_by_project_v1 AS abp
    ON p2p.artifact_id = abp.artifact_id
  WHERE
    p2p.ossd_project_name IN (
      SELECT DISTINCT ossd_name
      FROM oso.int_4337_address_labels
    )
    AND p2p.external_project_source = 'OP_ATLAS'
    AND abp.artifact_source = 'GITHUB'
),

artifact_flags AS (
  SELECT
    project_id,
    MAX(CASE WHEN artifact_type = 'DEFILLAMA_ADAPTER' THEN TRUE ELSE FALSE END) AS has_defillama_adapter,
    MAX(CASE WHEN artifact_type = 'BUNDLE_BEAR' THEN TRUE ELSE FALSE END) AS has_bundle_bear
  FROM artifacts
  GROUP BY 1
)

SELECT
  @measurement_date AS sample_date,
  builder_metrics.project_id,
  COALESCE(builder_metrics.transaction_count, 0) AS transaction_count,
  COALESCE(builder_metrics.gas_fees, 0.0)::DOUBLE AS gas_fees,
  COALESCE(builder_metrics.active_addresses_count, 0) AS active_addresses_count,
  COALESCE(builder_metrics.active_days, 0) AS active_days,
  builder_metrics.applied_to_round,
  project_eligibility.meets_all_criteria,
  (
    builder_metrics.applied_to_round
    AND project_eligibility.meets_all_criteria
  ) AS is_eligible,
  COALESCE(artifact_flags.has_defillama_adapter, FALSE)
    AS has_defillama_adapter, 
  COALESCE(artifact_flags.has_bundle_bear, FALSE)
    AS has_bundle_bear
FROM builder_metrics
JOIN project_eligibility
  ON builder_metrics.project_id = project_eligibility.project_id
LEFT JOIN artifact_flags
  ON builder_metrics.project_id = artifact_flags.project_id
