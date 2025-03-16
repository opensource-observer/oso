MODEL (
  name oso.int_deployers,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column block_timestamp,
    batch_size 365,
    batch_concurrency 1
  ),
  start @blockchain_incremental_start,
  partitioned_by (DAY("block_timestamp"), "chain")
);

SELECT
  block_timestamp,
  transaction_hash,
  deployer_address,
  contract_address,
  UPPER(chain) AS chain
FROM oso.stg_superchain__deployers