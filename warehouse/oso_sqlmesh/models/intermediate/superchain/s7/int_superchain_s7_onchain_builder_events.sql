MODEL(
  name oso.int_superchain_s7_onchain_builder_events,
  description 'Unified model of all Superchain-related events with S7-specific event weights',
  kind incremental_by_time_range(
   time_column time,
   batch_size 60,
   batch_concurrency 1,
   lookback 31
  ),
  start '2024-09-01',
  cron '@daily',
  dialect trino,
  partitioned_by (DAY("time"), "event_type", "event_source"),
  grain(
    time, event_type, event_source, project_id, from_artifact_id, transaction_hash
  ),
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


WITH projects AS (
  SELECT DISTINCT project_id
  FROM oso.projects_by_collection_v1
  WHERE
    collection_source = 'OP_ATLAS'
    AND collection_name IN ('8-1', '8-2', '8-3', '8-4', '8-5', '8-6')
),

all_events AS (
  SELECT
    e.project_id,
    e.time,
    e.event_type,
    e.event_source,
    e.from_artifact_id,
    e.transaction_hash,
    SUM(e.gas_fee) AS gas_fee,
    CASE
      WHEN e.event_type = 'CONTRACT_INVOCATION' THEN 1.0
      WHEN e.event_type = 'WORLDCHAIN_VERIFIED_USEROP' THEN 1.0
      WHEN e.event_type = 'WORLDCHAIN_NONVERIFIED_USEROP' THEN 1.0
      WHEN e.event_type = 'CONTRACT_INVOCATION_VIA_USEROP' THEN 1.0
      ELSE 0.5
    END AS event_weight
  FROM (
    SELECT
      project_id,
      time,
      event_type,
      event_source,
      from_artifact_id,
      transaction_hash,
      gas_fee
    FROM oso.int_superchain_events_by_project
    WHERE time BETWEEN @start_dt AND @end_dt
    UNION ALL
    SELECT
      project_id,
      time,
      event_type,
      event_source,
      from_artifact_id,
      transaction_hash,
      gas_fee
    FROM oso.int_worldchain_events_by_project
    WHERE time BETWEEN @start_dt AND @end_dt
  ) AS e
  JOIN projects AS p ON e.project_id = p.project_id
  GROUP BY
    e.project_id,
    e.time,
    e.event_type,
    e.event_source,
    e.from_artifact_id,
    e.transaction_hash
)

SELECT
  project_id,
  time,
  event_type,
  event_source,
  from_artifact_id,
  gas_fee,
  transaction_hash,
  event_weight
FROM (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY project_id, transaction_hash
      ORDER BY
        event_weight DESC,
        gas_fee DESC
    ) AS rn
  FROM all_events
)
WHERE rn = 1