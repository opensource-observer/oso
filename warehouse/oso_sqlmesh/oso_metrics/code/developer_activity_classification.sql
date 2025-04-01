select active.metrics_sample_date,
  active.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := active,
    include_column_alias := true,
  ),
  '' as from_artifact_id,
  @metric_name('full_time_developers') as metric,
  COUNT(DISTINCT active.from_artifact_id) as amount
from @metrics_peer_ref(
    developer_active_days,
    time_aggregation := @time_aggregation,
  ) as active
where active.amount / @metrics_sample_interval_length(active.metrics_sample_date, 'day') >= @full_time_ratio
group by metric,
  from_artifact_id,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := active,
  ),
  event_source,
  metrics_sample_date
union all
select active.metrics_sample_date,
  active.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := active,
    include_column_alias := true,
  ),
  '' as from_artifact_id,
  @metric_name('part_time_developers') as metric,
  COUNT(DISTINCT active.from_artifact_id) as amount
from @metrics_peer_ref(
    developer_active_days,
    time_aggregation := @time_aggregation,
  ) as active
where active.amount / @metrics_sample_interval_length(active.metrics_sample_date, 'day') < @full_time_ratio
group by metric,
  from_artifact_id,
  @metrics_entity_type_col('to_{entity_type}_id', table_alias := active),
  event_source,
  metrics_sample_date
union all
select active.metrics_sample_date,
  active.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := active,
    include_column_alias := true,
  ),
  '' as from_artifact_id,
  @metric_name('active_developers') as metric,
  COUNT(DISTINCT active.from_artifact_id) as amount
from @metrics_peer_ref(
    developer_active_days,
    time_aggregation := @time_aggregation,
  ) as active
group by metric,
  from_artifact_id,
  @metrics_entity_type_col('to_{entity_type}_id', table_alias := active),
  event_source,
  metrics_sample_date