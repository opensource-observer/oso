MODEL (
  name oso.int_superchain_s7_metrics,
  kind FULL,
  dialect trino,
);


@DEF(rewards_namespace, 'S7');
@DEF(timeseries_metrics, [
  'gas_fees',
  'transactions',
  'active_addresses',
  'defillama_tvl',
]);
@DEF(timeseries_agg_label, 'aggregation_daily');

WITH timeseries_metrics AS (
  SELECT metric
  FROM UNNEST(@timeseries_metrics) AS t(metric)
),

metric_combos AS (
  SELECT
    CONCAT(UPPER(chain), '_', metric, '_', @timeseries_agg_label)
      AS metric_name,
    CONCAT(metric, ' on ', chain) AS display_name,
    CONCAT('Daily total for `', metric, '` on `', chain, '` chain')
      AS description,
  FROM oso.int_superchain_chain_names
  CROSS JOIN timeseries_metrics
),

rewards_metrics AS (
  SELECT
    metric_name,
    display_name,
    description,
  FROM (VALUES
    (
      '8-1_reward',
      'OP Reward - Onchain Builders - Feb 2025',
      'Onchain Builders OP Reward for the Feb 2025 Measurement Period'
    ),
    (
      '8-1_eligibility',
      'Eligibility - Onchain Builders - Feb 2025',
      'Onchain Builders Eligibility for the Feb 2025 Measurement Period'
    )
  ) AS x (metric_name, display_name, description)
),

unioned_metrics AS (
  SELECT
    'OSO' AS metric_source,
    'oso' AS metric_namespace,
    metric_name,
    display_name,
    description,
  FROM metric_combos
  UNION ALL
  SELECT
    'OSO' AS metric_source,
    'retro-funding' AS metric_namespace,
    metric_name,
    display_name,
    description,
  FROM rewards_metrics
)

SELECT
  @oso_id(metric_source, metric_namespace, metric_name) AS metric_id,
  metric_source::VARCHAR,
  metric_namespace::VARCHAR,
  metric_name::VARCHAR,
  display_name::VARCHAR,
  description::VARCHAR,
  NULL::VARCHAR AS raw_definition,
  'TODO' AS definition_ref,
  'UNKNOWN' AS aggregation_function
FROM unioned_metrics