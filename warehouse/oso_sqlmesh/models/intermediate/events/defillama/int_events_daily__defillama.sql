MODEL (
  name oso.int_events_daily__defillama,
  description 'Unified daily DefiLlama event log with TVL, trading volume, and LP fee events',
  kind full,
  dialect trino,
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id),
  tags (
    'event_category=defillama'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH unioned_events AS (
  SELECT
    time,
    slug,
    protocol,
    chain,
    token,
    tvl AS amount,
    'DEFILLAMA_TVL' AS event_type
  FROM oso.stg_defillama__tvl_events
  UNION ALL
  SELECT
    time,
    slug,
    protocol,
    chain,
    token,
    amount,
    'DEFILLAMA_TRADING_VOLUME' AS event_type
  FROM oso.stg_defillama__trading_volume_events
  UNION ALL
  SELECT
    time,
    slug,
    protocol,
    chain,
    token,
    amount,
    'DEFILLAMA_LP_FEES' AS event_type
  FROM oso.stg_defillama__lp_fee_events
),

all_events AS (
  SELECT
    e.time,
    LOWER(e.slug) AS slug,
    e.protocol,
    LOWER(COALESCE(cl.oso_chain_name, REPLACE(e.chain, ' ', '_'))) AS chain,
    LOWER(e.token) AS token,
    e.amount,
    e.event_type
  FROM unioned_events AS e
  LEFT JOIN oso.seed_chain_alias_to_chain_name AS cl
    ON e.chain = cl.chain_alias
),

ranked_events AS (
  SELECT *,
    DATE_TRUNC('day', time) AS bucket_day,
    ROW_NUMBER() OVER (
      PARTITION BY 
        DATE_TRUNC('day', time),
        chain,
        slug,
        token,
        event_type
      ORDER BY time DESC
    ) as rn
  FROM all_events
),

filtered_events AS (
  SELECT
    bucket_day,
    event_type,
    chain,
    slug,
    token,
    amount
  FROM ranked_events
  WHERE
    rn = 1
    AND NOT (
      chain LIKE '%-borrowed'
      OR chain LIKE '%-vesting'
      OR chain LIKE '%-staking'
      OR chain LIKE '%-pool2'
      OR chain LIKE '%-treasury'
      OR chain LIKE '%-cex'
    )
    AND chain NOT IN (
      'treasury',
      'borrowed',
      'staking',
      'pool2',
      'polygon-bridge-&-staking'
    )
),

final_events_with_ids AS (
  SELECT
    bucket_day,
    event_type,
    'DEFILLAMA' AS event_source,
    @oso_id(
      bucket_day, 
      'DEFILLAMA', 
      '',              -- to_artifact_namespace
      slug,            -- to_artifact_name
      chain,           -- from_artifact_namespace
      token            -- from_artifact_name
    ) AS event_source_id,
    @oso_entity_id('DEFILLAMA', '', slug) AS to_artifact_id,
    '' AS to_artifact_namespace,
    slug AS to_artifact_name,
    @oso_entity_id('DEFILLAMA', chain, token) AS from_artifact_id,
    chain AS from_artifact_namespace,
    token AS from_artifact_name,
    amount::DOUBLE AS amount
  FROM filtered_events
)

SELECT
  *
FROM final_events_with_ids
