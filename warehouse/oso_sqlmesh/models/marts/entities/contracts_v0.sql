MODEL (
  name oso.contracts_v0,
  kind VIEW,
  tags (
    'export'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  column_descriptions (
    deployment_date = 'The date of a contract deployment',
    contract_address = 'The address of the contract',
    contract_namespace = 'The chain of the contract',
    originating_address = 'The EOA address that initiated the contract deployment transaction',
    factory_address = 'The address of the factory that deployed the contract, if this is the same as the originating address then this was a direct deployment by an EOA',
    root_deployer_address = 'The EOA address that is considered the root deployer of the contract. If the contract was deployed directly by an EOA, this should be the same as the originating address, if the contract was deployed by a factory this is the creator of the factory.',
    sort_weight = 'A weight used for sorting contracts. At this time, this is the tx count of the last 180 days'
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