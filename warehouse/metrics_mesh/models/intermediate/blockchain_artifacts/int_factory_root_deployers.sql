-- Root deployers is an interesting problem. When a contract gets created we
-- don't know if it's a factory based on our current processing. We can only
-- know that a contract is a factory if it has deployed other contracts. This
-- model is an attempt to identify the root deployer of a contract. The root
-- deployer is discovered by looking backwards through contract creators. To
-- prevent our warehouse from storing far too much data we only look back 365
-- days and incrementally update this model. If the contract is used as a
-- factory within that time and was also deployed within that time a row will be
-- created in this model. 
MODEL (
  name metrics.int_factory_root_deployers,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column deployment_date,
    batch_size 365,
    batch_concurrency 1
    --forward_only true
  ),
  partitioned_by (DAY("deployment_date"), "chain")
);

-- The model will use the last years of data to idenity the root deployer of a contract
with last_year_before_start as (
  select
    block_timestamp,
    originating_address,
    contract_address,
    factory_address,
    chain
  from metrics.int_factories
  where block_timestamp between @start_dt - INTERVAL 365 DAY and @end_dt
), current_processing as (
  select
    block_timestamp,
    originating_address,
    contract_address,
    factory_address,
    chain
  from metrics.int_factories
  where block_timestamp between @start_dt and @end_dt
)


select
  current.factory_address as factory_address,
  last_year.originating_address as root_deployer_address,
  current.chain as chain,
  last_year.block_timestamp as deployment_date
from current_processing as current
left join last_year_before_start as last_year
  on
    current.contract_address = last_year.factory_address
    and current.chain = last_year.chain