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
  start '2015-01-01',
  cron '@daily',
  partitioned_by DAY("sample_date"),
  grain (sample_date, project_id)
);

@DEF(lookback_days, 180);

@DEF(single_chain_tx_threshold, 10000);

@DEF(multi_chain_tx_threshold, 1000);

@DEF(gas_fees_threshold, 0.1);

@DEF(user_threshold, 420);

@DEF(active_days_threshold, 60);

WITH builder_metrics AS (
  SELECT
    project_id,
    COUNT(DISTINCT chain) AS chain_count,
    COUNT(DISTINCT transaction_hash) AS transaction_count,
    SUM(gas_fee) AS gas_fees,
    COUNT(DISTINCT from_artifact_id) AS user_count,
    COUNT(DISTINCT DATE_TRUNC('DAY', block_timestamp)) AS active_days
  FROM oso.int_superchain_trace_level_events_by_project
  WHERE
    block_timestamp BETWEEN @start_dt AND @end_dt
    AND CAST(block_timestamp AS DATE) >= (
      CURRENT_DATE - INTERVAL @lookback_days DAY
    )
  GROUP BY
    project_id
), project_eligibility AS (
  SELECT
    project_id,
    (
      (
        CASE
          WHEN chain_count > 1
          THEN transaction_count >= @multi_chain_tx_threshold
          ELSE transaction_count >= @single_chain_tx_threshold
        END
      )
      AND gas_fees >= @gas_fees_threshold
      AND user_count >= @user_threshold
      AND active_days >= @active_days_threshold
    ) AS is_eligible
  FROM builder_metrics
)
SELECT
  builder_metrics.project_id,
  builder_metrics.chain_count,
  builder_metrics.transaction_count,
  builder_metrics.gas_fees,
  builder_metrics.user_count,
  builder_metrics.active_days,
  project_eligibility.is_eligible,
  CURRENT_TIMESTAMP AS sample_date
FROM builder_metrics
INNER JOIN project_eligibility
  ON builder_metrics.project_id = project_eligibility.project_id