MODEL (
  name oso.int_events_daily__defillama_lp_fee,
  description 'Daily LP fee events from DefiLlama',
  kind FULL,
  dialect trino,
  partitioned_by (DAY("bucket_day"), "event_type"),
  grain (bucket_day, event_type, event_source, from_artifact_id, to_artifact_id),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH all_fee_events AS (
  SELECT * FROM oso.stg_defillama__lp_fee_events
),

ranked_fee_events AS (
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
  FROM all_fee_events
),

deduplicated_fee_events AS (
  SELECT
    bucket_day,
    chain,
    slug,
    token,
    amount
  FROM ranked_fee_events
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

lp_fee_events_with_ids AS (
  SELECT
    bucket_day,
    'DEFILLAMA_LP_FEES' AS event_type,
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
    amount::DOUBLE AS amount
  FROM deduplicated_fee_events
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
FROM lp_fee_events_with_ids
