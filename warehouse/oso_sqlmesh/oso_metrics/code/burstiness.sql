-- Calculate Fano Factor (variance^2/mean) as a measure of burstiness for repository activity
with activity_stats as (
  select
    @metrics_sample_date(events.bucket_day) as metrics_sample_date,
    events.event_source,
    events.to_artifact_id,
    avg(events.amount) over (
      partition by events.event_source, events.to_artifact_id 
      order by events.bucket_day 
      rows between unbounded preceding and current row
    ) as mean_activity,
    var_pop(events.amount) over (
      partition by events.event_source, events.to_artifact_id 
      order by events.bucket_day 
      rows between unbounded preceding and current row
    ) as variance_activity
  from oso.int_events_daily__github_with_zero_filling as events
  where
    events.bucket_day between @metrics_start('DATE') and @metrics_end('DATE')
)
select
  activity_stats.metrics_sample_date as metrics_sample_date,
  activity_stats.event_source as event_source,
  activity_stats.to_artifact_id as to_artifact_id,
  '' as from_artifact_id,
  @metric_name() as metric,
  cast(case 
   when mean_activity > 0 then variance_activity * variance_activity / mean_activity
    else -1
  end as DOUBLE) as amount
from activity_stats
