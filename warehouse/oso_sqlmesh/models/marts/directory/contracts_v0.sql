MODEL (
  name oso.contracts_v0,
  kind VIEW,
  tags (
    'export'
  ),
  audits (
    number_of_rows(threshold := 0)
  )
);

SELECT
  DATE_TRUNC('DAY', deployment_timestamp)::DATE AS deployment_date,
  contract_address,
  contract_namespace,
  originating_address,
  factory_address,
  root_deployer_address,
  sort_weight
FROM oso.int_contracts_overview