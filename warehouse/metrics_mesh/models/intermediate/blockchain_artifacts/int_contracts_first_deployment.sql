MODEL (
  name metrics.int_contracts_first_deployment,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 90,
    batch_concurrency 1,
    --forward_only true,
    --on_destructive_change warn
  ),
  start '2021-10-01',
  partitioned_by (DAY("block_timestamp"), "chain"),
);

-- The intent is to get the _first_ factory deployments as some contracts
-- deployed via deterministic deployers allows for multiple calls to the
-- create2 function.

with ordered_deployments_in_period as (
  select
    factories.block_timestamp as deployment_timestamp,
    factories.chain as chain,
    factories.transaction_hash as transaction_hash,
    factories.originating_address as originating_address,
    factories.contract_address as contract_address,
    factories.factory_address as factory_address,
    factories.create_type,
    row_number() over (
      partition by factories.contract_address, factories.chain
      order by block_timestamp asc
    ) as creation_order
  from metrics.int_factories as factories
  where contract_address is not null
    and block_timestamp between @start_dt and @end_dt
    -- ignore anything that already has already been processed
    and contract_address not in (
      select contract_address
      from @this_model
      where block_timestamp < @start_dt
    )
)
select 
  deployment_timestamp::TIMESTAMP,
  chain::VARCHAR,
  transaction_hash::VARCHAR,
  originating_address::VARCHAR,
  contract_address::VARCHAR,
  factory_address::VARCHAR,
  create_type::VARCHAR
from ordered_deployments_in_period
where creation_order = 1