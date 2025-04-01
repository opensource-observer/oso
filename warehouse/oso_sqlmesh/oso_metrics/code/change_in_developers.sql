select classification.metrics_sample_date,
  classification.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := classification
  ),
  '' as from_artifact_id,
  CASE WHEN classification.metric LIKE 'active_%' THEN @metric_name('change_in_active_developers')
    WHEN classification.metric LIKE 'full_%' THEN @metric_name('change_in_full_time_contributors')
    WHEN classification.metric LIKE 'part_%' THEN @metric_name('change_in_part_time_contributors')
  END as metric,
  LAG(classification.amount) OVER (
    PARTITION BY @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := classification
    ), classification.event_source, classification.metric
    ORDER BY classification.metrics_sample_date
  ) - classification.amount as amount

from @metrics_peer_ref(
    contributor_classifications,
    time_aggregation := @time_aggregation,
  ) as classification
-- group by classification.metrics_sample_date,
--   @metrics_entity_type_col(
--     'to_{entity_type}_id',
--     table_alias := classification
--   ),
--   classification.event_source,
--   5