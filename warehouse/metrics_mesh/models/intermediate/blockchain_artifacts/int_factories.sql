MODEL (
  name metrics.int_factories,
  kind VIEW
);

select
  block_timestamp,
  transaction_hash,
  originating_address,
  originating_contract,
  factory_address,
  contract_address,
  create_type,
  UPPER(chain) as chain 
from metrics.stg_superchain__factories