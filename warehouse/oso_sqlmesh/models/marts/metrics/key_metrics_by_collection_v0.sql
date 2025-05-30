MODEL (
  name oso.key_metrics_by_collection_v0,
  kind FULL,
  partitioned_by year(sample_date),
  tags (
    'export',
    'model_type=full',
    'model_category=metrics',
    'model_stage=mart',
    'entity_category=collection'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  description 'Each row represents a specific metric value for collection of projects at a recent date, capturing the metric type, the associated collection, the measured amount, and its unit. This data can be used to analyze trends and performance indicators across different collections for business insights such as growth, engagement, or risk. Business questions that can be answered include: Which collections currently have the most activity? How many contributors are currently involved in the collection?',
  column_descriptions (
    metric_id = 'The unique identifier for the metric, generated by OSO.',
    collection_id = 'The unique identifier for the collection, as generated by OSO.',
    sample_date = 'The date when the metric was sampled, truncated to the day. This is typically a recent date.',
    amount = 'The value of the metric for the collection on the sample date.',
    unit = 'The unit of measurement for the metric, if applicable.'
  )
);

WITH key_metrics_by_collection_v0_no_casting AS (
  SELECT
    @oso_id('OSO', 'oso', metric) AS metric_id,
    to_collection_id AS collection_id,
    metrics_sample_date AS sample_date,
    amount,
    metric,
    NULL AS unit
  FROM oso.key_metrics_to_collection
)
SELECT
  metric_id::TEXT,
  collection_id::TEXT,
  sample_date::DATE,
  amount::DOUBLE,
  unit::TEXT
FROM key_metrics_by_collection_v0_no_casting
