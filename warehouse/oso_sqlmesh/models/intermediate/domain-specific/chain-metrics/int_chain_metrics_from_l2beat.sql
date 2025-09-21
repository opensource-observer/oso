MODEL (
  name oso.int_chain_metrics_from_l2beat,
  description "Chain-level metrics from L2Beat",
  kind FULL,
  dialect trino,
  partitioned_by (DAY("sample_date"), "chain", "metric_name"),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH raw_metrics AS (
  -- TVS metrics from l2beat
  SELECT
    tvs.timestamp::DATE AS sample_date,
    tvs.project_slug,
    'L2BEAT_TVS_NATIVE' AS metric_name,
    tvs.native AS amount
  FROM oso.stg_l2beat__tvs AS tvs
  WHERE tvs.native IS NOT NULL

  UNION ALL

  SELECT
    tvs.timestamp::DATE AS sample_date,
    tvs.project_slug,
    'L2BEAT_TVS_CANONICAL' AS metric_name,
    tvs.canonical AS amount
  FROM oso.stg_l2beat__tvs AS tvs
  WHERE tvs.canonical IS NOT NULL

  UNION ALL

  SELECT
    tvs.timestamp::DATE AS sample_date,
    tvs.project_slug,
    'L2BEAT_TVS_EXTERNAL' AS metric_name,
    tvs.external AS amount
  FROM oso.stg_l2beat__tvs AS tvs
  WHERE tvs.external IS NOT NULL

  UNION ALL

  -- Activity metrics from l2beat
  SELECT
    activity.timestamp::DATE AS sample_date,
    activity.project_slug,
    'L2BEAT_ACTIVITY_COUNT' AS metric_name,
    activity.count AS amount
  FROM oso.stg_l2beat__activity AS activity
  WHERE activity.count IS NOT NULL

  UNION ALL

  SELECT
    activity.timestamp::DATE AS sample_date,
    activity.project_slug,
    'L2BEAT_ACTIVITY_UOPS_COUNT' AS metric_name,
    activity.uops_count AS amount
  FROM oso.stg_l2beat__activity AS activity
  WHERE activity.uops_count IS NOT NULL
),

final_metrics AS (
  SELECT
    raw_metrics.sample_date,
    UPPER(COALESCE(chain_alias.oso_chain_name, raw_metrics.project_slug))
      AS chain,
    raw_metrics.metric_name,
    raw_metrics.amount
  FROM raw_metrics
  LEFT JOIN oso.seed_chain_alias_to_chain_name AS chain_alias
    ON UPPER(raw_metrics.project_slug) = UPPER(chain_alias.chain_alias)
    AND chain_alias.source = 'l2beat'
),

deduplicated_metrics AS (
  SELECT
    sample_date,
    chain,
    metric_name,
    max_by(amount, sample_date) AS amount
  FROM final_metrics
  GROUP BY sample_date, chain, metric_name
)

SELECT
  sample_date,
  chain,
  metric_name,
  amount
FROM deduplicated_metrics
