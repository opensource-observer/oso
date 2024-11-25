select daa.metrics_sample_date,
  daa.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := daa,
    include_column_alias := true,
  ),
  '' as from_artifact_id,
  @metric_name('daily_active_addresses') as metric,
  COUNT(distinct daa.from_artifact_id) as amount
from @metrics_peer_ref(
    events_daily_to_artifact,
    window := @rolling_window,
    unit := @rolling_unit
  ) as daa
where daa.event_type in ('CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT')
  and daa.metrics_sample_date = @metrics_end('DATE')
group by metric,
  from_artifact_id,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := daa,
  ),
  event_source,
  metrics_sample_date
union all
select maa.metrics_sample_date,
  maa.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := maa,
    include_column_alias := true,
  ),
  '' as from_artifact_id,
  @metric_name('monthly_active_addresses') as metric,
  COUNT(distinct maa.from_artifact_id) as amount
from @metrics_peer_ref(
    events_daily_to_artifact,
    window := @rolling_window,
    unit := @rolling_unit
  ) as maa
where maa.event_type in ('CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT')
  and maa.metrics_sample_date between DATEADD(day, -29, @metrics_end('DATE')) 
    AND @metrics_end('DATE')
group by metric,
  from_artifact_id,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := maa,
  ),
  event_source,
  metrics_sample_date