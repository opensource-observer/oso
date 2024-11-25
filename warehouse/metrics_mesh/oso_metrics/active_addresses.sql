select @metrics_sample_date(events.bucket_day) as metrics_sample_date,
  events.event_source,
  events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name('daily_active_addresses') as metric,
  COUNT(distinct events.from_artifact_id) as amount
from metrics.events_daily_to_artifact as events
where event_type in ('CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT')
  and events.bucket_day = @metrics_sample_date('DATE')
group by 1,
  metric,
  from_artifact_id,
  to_artifact_id,
  event_source
union all
select @metrics_sample_date(events.bucket_day) as metrics_sample_date,
  events.event_source,
  events.to_artifact_id,
  '' as from_artifact_id,
  @metric_name('monthly_active_addresses') as metric,
  COUNT(distinct events.from_artifact_id) as amount
from metrics.events_daily_to_artifact as events
where event_type in ('CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT')
  and events.bucket_day BETWEEN DATEADD(day, -29, @metrics_sample_date('DATE')) 
    AND @metrics_sample_date('DATE') 
group by 1,
  metric,
  from_artifact_id,
  to_artifact_id,
  event_source