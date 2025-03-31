MODEL (
  name oso.int_events_daily__defillama_tvl,
  description 'Daily TVL events from DefiLlama',
  kind full,
  dialect trino,
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id)
);

WITH all_tvl_events AS (
  SELECT * FROM oso.stg_defillama__tvl_events
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
  WHERE
    rn = 1
    AND NOT (
      LOWER(chain) LIKE '%-borrowed'
      OR LOWER(chain) LIKE '%-vesting'
      OR LOWER(chain) LIKE '%-staking'
      OR LOWER(chain) LIKE '%-pool2'
      OR LOWER(chain) LIKE '%-treasury'
      OR LOWER(chain) LIKE '%-cex'
    )
    AND LOWER(chain) NOT IN (
      'treasury',
      'borrowed',
      'staking',
      'pool2',
      'polygon-bridge-&-staking'
    )
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
  FROM deduplicated_tvl_events
)

SELECT
  bucket_day,
  event_type,
  event_source,
  event_source_id,
  to_artifact_id,
  to_artifact_namespace,
  to_artifact_name,
  from_artifact_id,
  from_artifact_namespace,
  from_artifact_name,
  amount
FROM tvl_events_with_ids
