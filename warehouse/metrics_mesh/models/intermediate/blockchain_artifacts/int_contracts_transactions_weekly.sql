-- Part of the int_derived_contracts_transactions_weekly model. This is an
-- intermediate model that looks at the "universe" of blockchain traces and
-- attempts to give a summary of the activity on any given contract on a weekly
-- bucket. This is only used for the contracts overview model so it doesn't have
-- all of history

MODEL (
  name metrics.int_contracts_transactions_weekly,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column week,
    batch_size 180,
    batch_concurrency 3,
    --forward_only true,
    --on_destructive_change warn
  ),
  cron '@weekly',
  partitioned_by (DAY(week), chain),
  -- We only need to start a year before from the time we start using this
  -- model. We are using this as a way to categorize model ordering.
  start '2024-08-01'
);

-- Find all transactions involving the contracts from `derived_contracts` and
-- aggregate their tx_count on a weekly basis
select
  date_trunc('week', traces.dt) as week,
  upper(traces.chain) as chain,
  lower(traces.to_address) as contract_address,
  count(*) as tx_count
from @oso_source('bigquery.optimism_superchain_raw_onchain_data.traces') as traces
where 
  traces.network = 'mainnet'
  and "status" = 1
  and dt between @start_date and @end_date + INTERVAL 6 DAY
group by 1, 2, 3
