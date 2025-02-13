MODEL (
  name metrics.int_derived_contracts,
  kind VIEW
);

select
  deployment_timestamp::TIMESTAMP(6),
  chain::VARCHAR,
  originating_address::VARCHAR,
  contract_address::VARCHAR,
  factory_address::VARCHAR,
  create_type::VARCHAR,
  root_deployer_address::VARCHAR,
from metrics.int_contracts_root_deployers
