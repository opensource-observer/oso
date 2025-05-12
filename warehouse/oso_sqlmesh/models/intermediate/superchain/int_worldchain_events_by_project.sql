MODEL (
  name oso.int_worldchain_events_by_project,
  description 'Worldchain user events by project (both verified and non-verified)',
  kind incremental_by_time_range(
   time_column time,
   batch_size 60,
   batch_concurrency 1,
   lookback 31
  ),
  start '2024-09-01',
  cron '@daily',
  dialect trino,
  partitioned_by DAY("time"),
  grain (time, project_id, from_artifact_id, to_artifact_id),
  tags (
    'entity_category=project'
  ),
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := time,
      no_gap_date_part := 'day',
    ),
  )
);

WITH worldchain_contracts AS (
  SELECT DISTINCT
    project_id,
    artifact_id,
    artifact_name AS contract_address
  FROM oso.artifacts_by_project_v1
  WHERE artifact_source = 'WORLDCHAIN'
),

base_events AS (
  SELECT
    traces.block_timestamp AS time,
    traces.chain AS event_source,
    '' AS from_artifact_namespace,
    traces.from_address_trace AS from_artifact_name,
    worldchain_contracts.artifact_id AS to_artifact_id,
    worldchain_contracts.project_id,
    CASE 
      WHEN
        users.verified_address IS NOT NULL
        AND users.verified_until > traces.block_timestamp 
      THEN 'WORLDCHAIN_VERIFIED_USEROP'
      ELSE 'WORLDCHAIN_NONVERIFIED_USEROP'
    END AS event_type,
    traces.transaction_hash,
    traces.gas_used_trace * traces.gas_price_tx / 1e18 AS gas_fee
  FROM oso.int_superchain_traces_txs_joined AS traces
  JOIN worldchain_contracts
    ON traces.to_address_trace = worldchain_contracts.contract_address
  LEFT JOIN oso.int_worldchain_verified_addresses AS users
    ON traces.from_address_trace = users.verified_address
  WHERE
    traces.block_timestamp BETWEEN @start_dt AND @end_dt
    AND traces.chain = 'WORLDCHAIN'
)

SELECT
  time,
  event_type,
  event_source,
  to_artifact_id,
  @oso_entity_id(event_source, from_artifact_namespace, from_artifact_name)
    AS from_artifact_id,
  project_id,
  transaction_hash,
  gas_fee AS gas_fee
FROM base_events
