MODEL (
  name oso.int_contracts_overview,
  kind FULL,
  audits (
    number_of_rows(threshold := 0)
  )
);

SELECT
  derived_contracts.deployment_timestamp AS deployment_timestamp,
  derived_contracts.contract_address,
  derived_contracts.chain AS contract_namespace,
  derived_contracts.originating_address AS originating_address,
  derived_contracts.factory_address,
  derived_contracts.root_deployer_address AS root_deployer_address,
  sort_weights.sort_weight AS sort_weight
FROM oso.int_derived_contracts AS derived_contracts
INNER JOIN oso.int_derived_contracts_sort_weights AS sort_weights
  ON derived_contracts.contract_address = sort_weights.contract_address
  AND derived_contracts.chain = sort_weights.chain