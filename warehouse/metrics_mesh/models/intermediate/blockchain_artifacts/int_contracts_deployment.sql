MODEL (
  name metrics.int_contracts_deployment,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column deployment_timestamp,
    batch_size 90,
    batch_concurrency 1,
    --forward_only true,
    --on_destructive_change warn
  ),
  start '2021-10-01',
  partitioned_by (DAY("deployment_timestamp"), "chain"),
);

-- The intent is to get the _first_ factory deployments as some contracts
-- deployed via deterministic deployers allows for multiple calls to the
-- create2 function.



with ordered_deployments_in_period as (
  select
    factories.block_timestamp as deployment_timestamp,
    factories.chain as chain,
    factories.transaction_hash as transaction_hash,
    case 
      when proxies.address is not null then proxies.address
      else factories.originating_address
    end as originating_address,
    factories.originating_contract as originating_contract,
    factories.contract_address as contract_address,
    factories.factory_address as factory_address,
    factories.create_type,
    row_number() over (
      partition by factories.contract_address, factories.chain
      order by block_timestamp asc
    ) as creation_order,
    case 
      when proxies.address is not null then true
      else false
    end as is_proxy
  from metrics.int_factories as factories
  left join metrics.int_proxies as proxies
    on
      factories.originating_contract = proxies.address
      and factories.chain = proxies.chain
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
  create_type::VARCHAR,
  is_proxy::BOOLEAN
from ordered_deployments_in_period
where creation_order = 1