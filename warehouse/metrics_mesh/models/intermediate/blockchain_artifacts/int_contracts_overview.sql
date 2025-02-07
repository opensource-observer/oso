MODEL (
  name metrics.int_contracts_overview,
  kind FULL,
);

select
  derived_contracts.deployment_date as deployment_date,
  derived_contracts.contract_address,
  derived_contracts.chain as contract_namespace,
  derived_contracts.originating_address as originating_address,
  derived_contracts.factory_address,
  derived_contracts.root_deployer_address as root_deployer_address,
  sort_weights.sort_weight as sort_weight
from metrics.int_derived_contracts as derived_contracts
inner join metrics.int_derived_contracts_sort_weights as sort_weights
  on
    derived_contracts.contract_address = sort_weights.contract_address
    and derived_contracts.chain = sort_weights.chain

