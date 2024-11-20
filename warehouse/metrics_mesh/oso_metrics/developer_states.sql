select
  @metrics_sample_date(current.metrics_sample_date) as metrics_sample_date,
  current.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := current,
    include_column_alias := true,
  ),
  '' as from_artifact_id,
  @metric_name('developer_states') as metric,
  case 
    when prev.amount is null and current.amount > 0 then 'first_time'
    when current.amount / @rolling_window >= @full_time_ratio then 'full_time'
    when current.amount / @rolling_window < @full_time_ratio and current.amount > 0 then 'part_time'
    when prev.amount > 0 and current.amount = 0 then 'churned'
    else null
  end as state,
  current.amount as current_contributions,
  coalesce(prev.amount, 0) as previous_contributions
from
  @metrics_peer_ref(
    developer_active_days,
    window := @rolling_window,
    unit := @rolling_unit
  ) as current
left join
  @metrics_peer_ref(
    developer_active_days,
    window := @rolling_window,
    unit := @rolling_unit,
    offset := 1
  ) as prev
on
  current.metrics_sample_date = prev.metrics_sample_date
  and current.to_artifact_id = prev.to_artifact_id
  and current.event_source = prev.event_source
where
  current.metrics_sample_date = @metrics_end('DATE')
group by
  metrics_sample_date,
  metric,
  from_artifact_id,
  state,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := current,
  ),
  current.amount,
  prev.amount,
  current.event_source
