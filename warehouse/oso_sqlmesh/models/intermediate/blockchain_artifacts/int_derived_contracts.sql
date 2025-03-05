MODEL (
  name oso.int_derived_contracts,
  kind VIEW
);

SELECT
  deployment_timestamp::TIMESTAMP(6),
  chain::TEXT,
  originating_address::TEXT,
  contract_address::TEXT,
  factory_address::TEXT,
  create_type::TEXT,
  root_deployer_address::TEXT
FROM oso.int_contracts_root_deployers