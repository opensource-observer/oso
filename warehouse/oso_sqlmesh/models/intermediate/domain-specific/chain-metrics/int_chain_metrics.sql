MODEL(
  name oso.int_chain_metrics,
  description 'Chain metrics',
  dialect trino,
  kind full,
  partitioned_by (DAY("sample_date"), "chain", "metric_name"),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH gtp_metrics AS (
  SELECT
    gtp.date AS sample_date,
    'GROWTHEPIE' AS source,
    UPPER(COALESCE(chain_alias.oso_chain_name, gtp.origin_key)) AS chain,
    UPPER(gtp.metric_key) AS metric_name,
    gtp.value AS amount
  FROM oso.stg_growthepie__fundamentals_full AS gtp
  LEFT JOIN oso.seed_chain_alias_to_chain_name AS chain_alias
    ON UPPER(gtp.origin_key) = UPPER(chain_alias.chain_alias)
    AND chain_alias.source = 'growthepie'
),

defillama_metrics AS (
  SELECT
    dl.time::DATE AS sample_date,
    'DEFILLAMA' AS source,
    UPPER(COALESCE(chain_alias.oso_chain_name, dl.chain)) AS chain,
    'DEFILLAMA_TVL' AS metric_name,
    dl.tvl AS amount
  FROM oso.stg_defillama__historical_chain_tvl AS dl
  LEFT JOIN oso.seed_chain_alias_to_chain_name AS chain_alias
    ON UPPER(dl.chain) = UPPER(chain_alias.chain_alias)
    AND chain_alias.source = 'defillama'
),

l2beat_metrics AS (
  SELECT
    sample_date,
    'L2BEAT' AS source,
    chain,
    metric_name,
    amount
  FROM oso.int_chain_metrics_from_l2beat
),

oso_metrics AS (
  SELECT
    sample_date,
    'OSO' AS source,
    chain,
    metric_name,
    amount
  FROM oso.int_chain_metrics_from_oso
  WHERE (
    -- TODO: remove once we have support for custom gas tokens
    chain != 'CELO'
    AND metric_name != 'LAYER2_GAS_FEES'
  )
),

union_metrics AS (
  SELECT * FROM gtp_metrics
  UNION ALL
  SELECT * FROM defillama_metrics
  UNION ALL
  SELECT * FROM l2beat_metrics
  UNION ALL
  SELECT * FROM oso_metrics
)

SELECT
  sample_date,
  source,
  chain,
  metric_name,
  amount
FROM union_metrics