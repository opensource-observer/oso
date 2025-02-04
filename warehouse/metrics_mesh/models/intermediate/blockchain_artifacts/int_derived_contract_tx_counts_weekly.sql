-- In order to keep this model as small and the least complicated it can be we
-- take the last 180 days and aggregate activity on a given contract on a weekly
-- basis when used in the contracts overview model. This model is intermediate
-- to that model and simply aggregates the transactions on a weekly basis for a
-- given contract. It only goes back ~6 months from the time we deployed this
-- model (2025-02-01)

-- In the future we should make a different model type for this that
-- automatically deletes _old_ data that we don't need. However sqlmesh doesn't
-- have out of the box support for that yet so we will implement as an
-- INCREMENTAL_BY_TIME_RANGE model for now.

MODEL (
  name metrics.int_derived_contracts_transactions_weekly,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column week,
    batch_size 365,
    batch_concurrency 1,
    --forward_only true,
    --on_destructive_change warn
  ),
  cron '@weekly',
  partitioned_by DAY(week),
  -- We only need to start a year before from the time we start using this
  -- model. We are using this as a way to categorize model ordering.
  start '2024-08-01'
);

-- Find all transactions involving the contracts from `derived_contracts` and
-- aggregate their tx_count on a weekly basis
select
  date_trunc('week', dt) as week,
  UPPER(derived_contracts.chain) as chain,
  contract_address,
  count(*) as tx_count
from @oso_source('bigquery.optimism_superchain_raw_onchain_data.traces') as traces
inner join metrics.int_derived_contracts as derived_contracts
  on traces.to_address = derived_contracts.contract_address
  and traces.chain = derived_contracts.chain
where 
  traces.network = 'mainnet'
  and "status" = 1
  and dt between @start_date and @end_date
group by 1, 2, 3
