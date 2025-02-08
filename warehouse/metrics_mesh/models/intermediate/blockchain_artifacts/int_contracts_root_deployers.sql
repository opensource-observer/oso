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
    batch_size 30,
    batch_concurrency 1,
    lookback 30
    --forward_only true
  ),
  partitioned_by (DAY("deployment_date"), "chain")
);

-- Take all of the contracts deployed up till now and find the root deployer
-- recursively once we find an originating address that is not a contract
-- address we know we have found the root deployer
with existing_contracts as (
  select * 
  from @this_model
  where deployment_timestamp < @start_dt
), new_contracts as (
  select
    *
  from metrics.int_contracts_factory_deployed
  where deployment_timestamp between @start_dt and @end_dt
), new_resolved as (
  select
    new.deployment_timestamp,
    new.chain,
    new.transaction_hash,
    new.originating_address,
    new.contract_address,
    new.factory_address,
    new.create_type,
    existing.root_deployer_address,
    existing.depth + 1 as depth
  from new_contracts as new
  inner join existing_contracts as existing
    on
      new.chain = existing.chain
      and new.factory_address = existing.contract_address
  where 
    existing.root_deployer_address is not null
), all_resolved as (
  select * from new_resolved as new
  union all
  select * from existing_contracts
), new_unresolved as (
  select * from new_contracts
  where contract_address not in (
    select contract_address from all_resolved 
  )
), recursive root_deployers as (
  select
    deployment_date,
    chain,
    originating_address,
    contract_address,
    factory_address,
    NULL as root_deployer_address,
    0 as depth
  from new_unresolved

  union all

  -- The only time we will have a NULL root deployer address is if we have never
  -- resolved that contract's root deployer before. So that means either:
  --   1. The graph of this contract was deployed in the last period of time
  --   2. The graph of this contract is somehow missing
  -- The hope is because this is an incremental model we will eventually resolve
  -- all of the contracts' root deployers. 

  select
    recursed.deployment_date,
    recursed.chain,
    recursed.originating_address,
    recursed.contract_address,
    recursed.factory_address,
    new.
    recursed.depth + 1 as depth
  from new_unresolved as new 
  inner join root_deployers as recursed
    on
      recursed.chain = new.chain
      and recursed.factory_address = new.contract_address
      and recursed.depth < 4
)
