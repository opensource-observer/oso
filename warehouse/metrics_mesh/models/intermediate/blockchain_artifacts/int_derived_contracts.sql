MODEL (
  name metrics.int_derived_contracts,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column deployment_date,
    batch_size 365,
    batch_concurrency 1,
    --forward_only true,
    --on_destructive_change allow
  ),
  partitioned_by (DAY("deployment_date"), "chain"),
  cron '@daily',
);

with contracts_deployed_no_factory as (
  select
    block_timestamp as deployment_date,
    chain,
    deployer_address as originating_address,
    contract_address,
    '' as factory_address,
    deployer_address as root_deployer_address
  from metrics.int_deployers
  where contract_address is not null
    and block_timestamp between @start_dt and @end_dt
),

contracts_deployed_via_factory as (
  -- This gets all of the contracts deployed by any factory.
  -- Deployer Address is the EOA address that started the transaction
  select
    block_timestamp as deployment_date,
    factories.chain,
    originating_address as originating_address,
    contract_address as contract_address,
    factories.factory_address as factory_address,
    factory_root_deployers.root_deployer_address as root_deployer_address
  from metrics.int_factories as factories
  inner join metrics.int_factory_root_deployers as factory_root_deployers
    on
      factory_root_deployers.factory_address = factories.factory_address
      and factories.chain = factory_root_deployers.chain
  where contract_address is not null
    and block_timestamp between @start_dt and @end_dt
),

contracts_deployed_by_safe_or_known_proxy as (
  -- This gets all of the contracts deployed by a safe or other known proxy
  -- Deployer address is a proxy (safe or other known proxy) that deployed the contract
  select
    factories.block_timestamp as deployment_date,
    factories.chain,
    proxies.address as originating_address,
    factories.contract_address as contract_address,
    factories.factory_address as factory_address,
    factory_root_deployers.root_deployer_address as root_deployer_address
  from metrics.int_factories as factories
  inner join metrics.int_proxies as proxies
    on
      factories.originating_contract = proxies.address
      and factories.chain = proxies.chain
  inner join metrics.int_factory_root_deployers as factory_root_deployers
    on
      factory_root_deployers.factory_address = factories.factory_address
      and factories.chain = factory_root_deployers.chain
  where contract_address is not null
    and factories.block_timestamp between @start_dt and @end_dt
),

derived_contracts as (
  select
    deployment_date,
    chain,
    originating_address,
    contract_address,
    factory_address,
    root_deployer_address
  from contracts_deployed_no_factory

  union all

  select
    deployment_date,
    chain,
    originating_address,
    contract_address,
    factory_address,
    root_deployer_address
  from contracts_deployed_via_factory

  union all

  select
    deployment_date,
    chain,
    originating_address,
    contract_address,
    factory_address,
    root_deployer_address
  from contracts_deployed_by_safe_or_known_proxy
)

select distinct
  deployment_date,
  chain,
  originating_address,
  contract_address,
  factory_address,
  root_deployer_address
from derived_contracts
