MODEL (
  name metrics.int_contracts_overview,
  kind FULL,
);

@DEF(start, current_date() - INTERVAL 180 DAY);
@DEF(end, current_date());

select
  MIN(derived_contracts.deployment_date) as deployment_date,
  derived_contracts.contract_address,
  derived_contracts.chain as contract_namespace,
  derived_contracts.originating_address as originating_address,
  derived_contracts.factory_address,
  derived_contracts.root_deployer_address as root_deployer_address,
  SUM(transactions_weekly.tx_count) as sort_weight
from metrics.int_derived_contracts as derived_contracts
inner join metrics.int_derived_contracts_transactions_weekly as transactions_weekly
  on
    derived_contracts.contract_address = transactions_weekly.contract_address
    and derived_contracts.chain = transactions_weekly.chain
where derived_contracts.deployment_date between @start and @end
group by
  derived_contracts.contract_address,
  derived_contracts.chain,
  derived_contracts.factory_address,
  derived_contracts.root_deployer_address,
  derived_contracts.originating_address


