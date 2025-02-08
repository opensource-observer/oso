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
  name metrics.int_contracts_root_deployers,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column deployment_timestamp,
    batch_size 90,
    batch_concurrency 1,
    lookback 30
    --forward_only true
  ),
  start '2021-10-01',
  partitioned_by (DAY("deployment_timestamp"), "chain")
);

with existing_contracts as (
  select * 
  from @this_model
  where deployment_timestamp < @start_dt
), new_contracts as (
  select
    deployment_timestamp,
    chain,
    transaction_hash,
    originating_address,
    contract_address,
    -- if the originating address is the same as the factory address then
    -- this was a create_type of create and deployed directly by an EOA
    case
      when originating_address = factory_address then null
      else factory_address
    end as factory_address,
    create_type,
    case 
      -- for create deployed factories we can just use the originating address
      when originating_address = factory_address then originating_address
      when is_proxy then originating_address
      else null
    end as root_deployer_address,
    0 as depth
  from metrics.int_contracts_deployment
  where deployment_timestamp between @start_dt and @end_dt
), all_contracts as (
  select * from existing_contracts
  union all 
  select * from new_contracts
), new_resolved as (
  select
    new.deployment_timestamp,
    new.chain,
    new.transaction_hash,
    new.originating_address,
    new.contract_address,
    new.factory_address,
    new.create_type,
    case 
      when new.root_deployer_address is not null then new.root_deployer_address
      else all.originating_address
    end as root_deployer_address,
    case
      when all.depth is not null then all.depth + 1
      else new.depth
    end as depth
  from new_contracts as new
  left join all_contracts as all 
    on
      all.chain = new.chain
      and all.contract_address = new.factory_address
)
select 
  deployment_timestamp::TIMESTAMP,
  chain::VARCHAR,
  transaction_hash::VARCHAR,
  originating_address::VARCHAR,
  contract_address::VARCHAR,
  factory_address::VARCHAR,
  create_type::VARCHAR,
  root_deployer_address::VARCHAR,
  depth::INT
from new_resolved

