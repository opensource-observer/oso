MODEL (
  name oso.int_events_daily__defillama_tvl,
  description 'Daily TVL events from DefiLlama',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 365,
    batch_concurrency 1
  ),
  start @defillama_incremental_start,
  cron '@daily',
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id)
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

tvl_events_with_ids AS (
  SELECT
    bucket_day,
    'DEFILLAMA_TVL' AS event_type,
    UPPER(chain) AS event_source,
    @oso_id(
      bucket_day, 
      UPPER(chain), 
      'defillama', -- to_artifact_namespace
      LOWER(slug), -- to_artifact_name
      'defillama', -- from_artifact_namespace
      LOWER(token) -- from_artifact_name
    ) AS event_source_id,
    @oso_id('DEFILLAMA', '', LOWER(slug)) AS to_artifact_id,
    'defillama' AS to_artifact_namespace,
    LOWER(slug) AS to_artifact_name,
    @oso_id('DEFILLAMA', '', LOWER(token)) AS from_artifact_id,
    'defillama' AS from_artifact_namespace,
    LOWER(token) AS from_artifact_name,
    tvl::DOUBLE AS amount
  FROM deduplicated_tvl_events
)

SELECT DISTINCT
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
LEFT OUTER JOIN oso.artifacts_by_project_v1 AS abp
  ON tvl_events_with_ids.to_artifact_id = abp.artifact_id