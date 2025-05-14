/* Root deployers is an interesting problem. When a contract gets created we */ /* don't know if it's a factory based on our current processing. We can only */ /* know that a contract is a factory if it has deployed other contracts. This */ /* model is an attempt to identify the root deployer of a contract. The root */ /* deployer is discovered by looking backwards through contract creators. To */ /* prevent our warehouse from storing far too much data we only look back 365 */ /* days and incrementally update this model. If the contract is used as a */ /* factory within that time and was also deployed within that time a row will be */ /* created in this model. */
MODEL (
  name oso.int_contracts_root_deployers,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column deployment_timestamp,
    batch_size 90,
    batch_concurrency 1,
    lookback 31
  ) /* forward_only true */,
  start @blockchain_incremental_start,
  partitioned_by (DAY("deployment_timestamp"), "chain"),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := deployment_timestamp,
      no_gap_date_part := 'day',
      ignore_before := @superchain_audit_start,
      missing_rate_min_threshold := 0.95,
    ),
  )
);

WITH existing_contracts AS (
  SELECT
    *
  FROM @this_model
  WHERE
    deployment_timestamp < @start_dt
), new_contracts AS (
  SELECT
    deployment_timestamp,
    chain,
    transaction_hash,
    originating_address,
    contract_address,
    CASE WHEN originating_address = factory_address THEN NULL ELSE factory_address END AS factory_address, /* if the originating address is the same as the factory address then */ /* this was a create_type of create and deployed directly by an EOA */
    create_type,
    CASE
      WHEN originating_address = factory_address
      THEN originating_address
      WHEN is_proxy
      THEN originating_address
      ELSE NULL
    END AS root_deployer_address,
    0 AS depth
  FROM oso.int_contracts_deployment
  WHERE
    deployment_timestamp BETWEEN @start_dt AND @end_dt
), all_contracts AS (
  SELECT
    *
  FROM existing_contracts
  UNION ALL
  SELECT
    *
  FROM new_contracts
), new_resolved AS (
  SELECT
    new.deployment_timestamp,
    new.chain,
    new.transaction_hash,
    new.originating_address,
    new.contract_address,
    new.factory_address,
    new.create_type,
    CASE
      WHEN NOT new.root_deployer_address IS NULL
      THEN new.root_deployer_address
      ELSE "all".originating_address
    END AS root_deployer_address,
    CASE WHEN NOT "all".depth IS NULL THEN "all".depth + 1 ELSE new.depth END AS depth
  FROM new_contracts AS new
  LEFT JOIN all_contracts AS "all"
    ON "all".chain = new.chain AND "all".contract_address = new.factory_address
)
SELECT
  deployment_timestamp::TIMESTAMP,
  chain::TEXT,
  transaction_hash::TEXT,
  originating_address::TEXT,
  contract_address::TEXT,
  factory_address::TEXT,
  create_type::TEXT,
  root_deployer_address::TEXT,
  depth::INT
FROM new_resolved