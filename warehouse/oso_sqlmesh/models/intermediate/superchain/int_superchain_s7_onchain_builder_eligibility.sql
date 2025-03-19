/* TODO: turn this into a rolling model that includes a sample date (eg, every week) */
MODEL (
  name oso.int_superchain_s7_onchain_builder_eligibility,
  description "Determines if a project is eligible for measurement in the S7 onchain builder round",
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

@DEF(measurement_date, DATE('2025-03-01'));
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
    SUM(events.gas_fee) AS gas_fees,
    MAX(CASE WHEN events.event_source = 'WORLDCHAIN' THEN true ELSE false END) AS is_worldchain_app
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
      transaction_count >= @transactions_threshold
      AND active_days >= @days_with_onchain_activity_threshold
      AND gas_fees >= @gas_fees_threshold
      AND (
        active_addresses_count >= @active_addresses_threshold
        OR is_worldchain_app -- worldchain natively bundles userops
      )
    ) AS meets_all_criteria
  FROM builder_metrics
)

SELECT
  @measurement_date AS sample_date,
  builder_metrics.project_id,
  COALESCE(builder_metrics.transaction_count, 0) AS transaction_count,
  COALESCE(builder_metrics.gas_fees, 0) AS gas_fees,
  COALESCE(builder_metrics.active_addresses_count, 0) AS active_addresses_count,
  COALESCE(builder_metrics.active_days, 0) AS active_days,
  builder_metrics.applied_to_round,
  builder_metrics.is_worldchain_app,
  project_eligibility.meets_all_criteria,
  (
    builder_metrics.applied_to_round
    AND project_eligibility.meets_all_criteria
  ) AS is_eligible
FROM builder_metrics
JOIN project_eligibility
  ON builder_metrics.project_id = project_eligibility.project_id