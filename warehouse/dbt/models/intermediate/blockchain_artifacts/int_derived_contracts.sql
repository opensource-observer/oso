with factories_and_deployers as (
  select
    factories.block_timestamp,
    factories.transaction_hash,
    factories.network,
    factories.originating_address as deployer_address,
    factories.contract_address as contract_address
  from {{ ref("int_factories") }} as factories
  inner join {{ ref("int_deployers") }} as deployers
    on
      factories.factory_address = deployers.contract_address
      and factories.network = deployers.network
  union all
  select
    block_timestamp,
    transaction_hash,
    network,
    deployer_address,
    contract_address
  from {{ ref("int_deployers") }}
),

factories_and_proxies as (
  select
    factories.block_timestamp,
    factories.transaction_hash,
    factories.network,
    proxies.address as deployer_address,
    factories.contract_address as contract_address
  from {{ ref("int_factories") }} as factories
  inner join {{ ref("int_proxies") }} as proxies
    on
      factories.originating_address = proxies.address
      and factories.network = proxies.network
)

select
  block_timestamp,
  transaction_hash,
  network,
  deployer_address,
  contract_address
from factories_and_deployers
union all
select
  block_timestamp,
  transaction_hash,
  network,
  deployer_address,
  contract_address
from factories_and_proxies
