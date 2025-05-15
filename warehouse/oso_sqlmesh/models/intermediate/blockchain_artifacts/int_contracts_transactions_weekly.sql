/* Part of the int_derived_contracts_transactions_weekly model. This is an */ /* intermediate model that looks at the "universe" of blockchain traces and */ /* attempts to give a summary of the activity on any given contract on a weekly */ /* bucket. This is only used for the contracts overview model so it doesn't have */ /* all of history */
MODEL (
  name oso.int_contracts_transactions_weekly,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column week,
    batch_size 180,
    batch_concurrency 3,
    lookback 31,
    forward_only true,
    on_destructive_change warn,
  ),
  cron '@weekly',
  partitioned_by (DAY(week), chain),
  start '2024-08-01',
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  -- This model is weekly so this can't work for now
  ignored_rules (
    "incrementalmustdefinenogapsaudit",
  ),
);

/* Find all transactions involving the contracts from `derived_contracts` and */ /* aggregate their tx_count on a weekly basis */
SELECT
  DATE_TRUNC('WEEK', traces.dt) AS week,
  @chain_name(traces.chain) AS chain,
  LOWER(traces.to_address) AS contract_address,
  COUNT(*) AS tx_count
FROM @oso_source('bigquery.optimism_superchain_raw_onchain_data.traces') AS traces
WHERE
  traces.network = 'mainnet'
  AND "status" = 1
  AND dt BETWEEN @start_date AND @end_date + INTERVAL '6' DAY
GROUP BY
  1,
  2,
  3