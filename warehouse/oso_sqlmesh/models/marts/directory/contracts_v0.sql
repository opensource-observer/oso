MODEL (
  name metrics.contracts_v0,
  kind VIEW,
  tags (
    'export'
  ),
);

select
  date_trunc('day', deployment_timestamp)::DATE as deployment_date,
  contract_address,
  contract_namespace,
  originating_address,
  factory_address,
  root_deployer_address,
  sort_weight
from metrics.int_contracts_overview