MODEL (
  name oso.int_chain_metrics_from_growthepie,
  description "Chain-level metrics from growthepie",
  kind FULL,
  dialect trino,
  partitioned_by (DAY("sample_date"), "chain", "metric_name"),
  grain (sample_date, chain, metric_name),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH gtp_metrics AS (
  SELECT
    gtp.date AS sample_date,
    UPPER(COALESCE(chain_alias.oso_chain_name, gtp.origin_key)) AS chain,
    UPPER(gtp.metric_key) AS metric_name,
    gtp.value AS amount
  FROM oso.stg_growthepie__fundamentals_full AS gtp
  LEFT JOIN oso.seed_chain_alias_to_chain_name AS chain_alias
    ON UPPER(gtp.origin_key) = UPPER(chain_alias.chain_alias)
    AND chain_alias.source = 'growthepie'
)

SELECT
  sample_date,
  chain,
  metric_name,
  amount
FROM gtp_metrics