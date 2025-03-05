MODEL (
  name oso.int_factories,
  kind VIEW
);

SELECT
  block_timestamp,
  transaction_hash,
  originating_address,
  originating_contract,
  factory_address,
  contract_address,
  create_type,
  UPPER(chain) AS chain
FROM oso.stg_superchain__factories