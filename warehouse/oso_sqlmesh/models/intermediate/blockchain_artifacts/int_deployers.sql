MODEL (
  name metrics.int_deployers,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 365,
    batch_concurrency 1
  ),
  start '2021-10-01',
  partitioned_by (DAY("block_timestamp"), "chain"),
);

select 
  block_timestamp,
  transaction_hash,
  deployer_address,
  contract_address,
  UPPER(chain) as chain 
from metrics.stg_superchain__deployers