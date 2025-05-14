MODEL (
  name oso.int_contracts_deployment,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column deployment_timestamp,
    batch_size 90,
    batch_concurrency 1,
    lookback 31
  ) /* forward_only true, */ /* on_destructive_change warn */,
  start @blockchain_incremental_start,
  partitioned_by (DAY("deployment_timestamp"), "chain"),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := deployment_timestamp,
      no_gap_date_part := 'day',
      ignore_before := @superchain_audit_start,
    ),
  )
);

/* The intent is to get the _first_ factory deployments as some contracts */ /* deployed via deterministic deployers allows for multiple calls to the */ /* create2 function. */
WITH ordered_deployments_in_period AS (
  SELECT
    factories.block_timestamp AS deployment_timestamp,
    factories.chain AS chain,
    factories.transaction_hash AS transaction_hash,
    CASE
      WHEN NOT proxies.address IS NULL
      THEN proxies.address
      ELSE factories.originating_address
    END AS originating_address,
    factories.originating_contract AS originating_contract,
    factories.contract_address AS contract_address,
    factories.factory_address AS factory_address,
    factories.create_type,
    ROW_NUMBER() OVER (PARTITION BY factories.contract_address, factories.chain ORDER BY block_timestamp ASC) AS creation_order,
    CASE WHEN NOT proxies.address IS NULL THEN TRUE ELSE FALSE END AS is_proxy
  FROM oso.int_factories AS factories
  LEFT JOIN oso.int_proxies AS proxies
    ON factories.originating_contract = proxies.address
    AND factories.chain = proxies.chain
  WHERE
    NOT contract_address IS NULL
    AND block_timestamp BETWEEN @start_dt AND @end_dt
    AND /* ignore anything that already has already been processed */ NOT contract_address IN (
      SELECT
        contract_address
      FROM @this_model
      WHERE
        block_timestamp < @start_dt
    )
)
SELECT
  deployment_timestamp::TIMESTAMP,
  chain::TEXT,
  transaction_hash::TEXT,
  originating_address::TEXT,
  contract_address::TEXT,
  factory_address::TEXT,
  create_type::TEXT,
  is_proxy::BOOLEAN
FROM ordered_deployments_in_period
WHERE
  creation_order = 1