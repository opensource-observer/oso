MODEL (
  name oso.int_chain_metrics_from_defillama,
  description "Chain-level metrics from DefiLlama",
  kind FULL,
  dialect trino,
  grain (sample_date, chain, metric_name),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH defillama_metrics AS (
  SELECT
    dl.time::DATE AS sample_date,
    UPPER(COALESCE(chain_alias.oso_chain_name, dl.chain)) AS chain,
    'DEFILLAMA_TVL' AS metric_name,
    dl.tvl AS amount
  FROM oso.stg_defillama__historical_chain_tvl AS dl
  LEFT JOIN oso.seed_chain_alias_to_chain_name AS chain_alias
    ON UPPER(dl.chain) = UPPER(chain_alias.chain_alias)
    AND chain_alias.source = 'defillama'
)

SELECT
  sample_date,
  chain,
  metric_name,
  amount
FROM defillama_metrics