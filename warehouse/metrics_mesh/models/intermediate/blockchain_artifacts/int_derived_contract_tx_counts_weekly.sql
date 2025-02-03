-- In order to keep this model as small and the least complicated it can be we
-- take the last 180 days and aggregate activity on a given contract on a weekly
-- basis. 

-- In the future we should make a different model type for this that
-- automatically deletes _old_ data that we don't need. However to keep this a
-- small operation this intermediate model will run continously every day and be
-- used by another model downstream to calculate the _current_ sorting order

MODEL (
  name metrics.int_derived_contracts_transactions_weekly
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 1
  ),
  -- We only need to start a year before from the time we start using this
  -- model. We are using this as a way to categorize model ordering.
  start '2024-02-03'
);

-- Find all transactions involving the contracts from `derived_contracts` and
-- aggregate them on a weekly basis
select
  date_trunc('week', dt) as week,
  contract_address,
  count(*) as tx_count
from @oso_source('bigquery.optimism_superchain_raw_onchain_data.traces') as traces
inner join metrics.int_derived_contracts as derived_contracts
  on traces.contract_address = derived_contracts.contract_address
where 
  network = 'mainnet'
  and "status" = 1
  and dt between @start_date and @end_date
group by 1, 2
