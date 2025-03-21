MODEL (
  name oso.int_events_daily__defillama_tvl,
  description 'Daily TVL events from DefiLlama',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 365,
    batch_concurrency 1
  ),
  start @defillama_incremental_start,
  dialect trino,
  cron '@daily',
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id, project_id)
);

WITH all_tvl_events AS (
  SELECT * FROM oso.stg__defillama_tvl_events
),

ranked_tvl_events AS (
  SELECT *,
    DATE_TRUNC('day', time) AS bucket_day,
    ROW_NUMBER() OVER (
      PARTITION BY 
        DATE_TRUNC('day', time),
        chain,
        slug,
        token
      ORDER BY time DESC
    ) as rn
  FROM all_tvl_events
),

deduplicated_tvl_events AS (
  SELECT
    bucket_day,
    chain,
    slug,
    token,
    tvl
  FROM ranked_tvl_events
  WHERE rn = 1
),

merged_tvl_events AS (
  SELECT
    bucket_day,
    chain,
    slug,
    token,
    tvl
  FROM deduplicated_tvl_events
  UNION ALL
  SELECT
    bucket_day::DATE as bucket_day,
    chain,
    slug,
    token,
    amount as tvl
  FROM oso.int_events_daily__defillama_tvl_upload
),

tvl_events_with_ids AS (
  SELECT
    bucket_day,
    'DEFILLAMA_TVL' AS event_type,
    'DEFILLAMA' AS event_source,
    @oso_id(
      bucket_day, 
      'DEFILLAMA', 
      '',           -- to_artifact_namespace
      LOWER(slug),  -- to_artifact_name
      LOWER(chain), -- from_artifact_namespace
      LOWER(token)  -- from_artifact_name
    ) AS event_source_id,
    @oso_entity_id('DEFILLAMA', '', LOWER(slug)) AS to_artifact_id,
    '' AS to_artifact_namespace,
    LOWER(slug) AS to_artifact_name,
    @oso_entity_id('DEFILLAMA', LOWER(chain), LOWER(token)) AS from_artifact_id,
    LOWER(chain) AS from_artifact_namespace,
    LOWER(token) AS from_artifact_name,
    tvl::DOUBLE AS amount
  FROM merged_tvl_events
)

-- This will create a row for each project associated with the artifact
SELECT
  abp.project_id,
  tvl_events_with_ids.bucket_day,
  tvl_events_with_ids.event_type,
  tvl_events_with_ids.event_source,
  tvl_events_with_ids.event_source_id,
  tvl_events_with_ids.to_artifact_id,
  tvl_events_with_ids.to_artifact_namespace,
  tvl_events_with_ids.to_artifact_name,
  tvl_events_with_ids.from_artifact_id,
  tvl_events_with_ids.from_artifact_namespace,
  tvl_events_with_ids.from_artifact_name,
  tvl_events_with_ids.amount
FROM tvl_events_with_ids
INNER JOIN oso.artifacts_by_project_v1 AS abp
  ON tvl_events_with_ids.to_artifact_id = abp.artifact_id
