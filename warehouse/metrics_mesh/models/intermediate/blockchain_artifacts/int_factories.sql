MODEL (
  name metrics.int_factories,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 365,
    batch_concurrency 1
  ),
  partitioned_by (DAY("block_timestamp"), "network"),
);

select
  block_timestamp,
  transaction_hash,
  originating_address,
  originating_contract,
  factory_address,
  contract_address,
  UPPER(chain) as network
from metrics.stg_superchain__factories