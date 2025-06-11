-- Calculate Fano Factor (variance^2/mean) as a measure of burstiness for repository activity
-- Manual handling of zero-filled dates using formulas: Average = SUM/COUNT, VAR_POP = SUM(amount^2-mean^2)/COUNT
with activity_stats as (
  select
    @metrics_sample_date(events.bucket_day) as metrics_sample_date,
    events.event_source,
    events.to_artifact_id,
    sum(events.amount) over (
      partition by events.event_source, events.to_artifact_id 
      order by events.bucket_day 
      rows between unbounded preceding and current row
    ) as cumulative_sum,
      events.bucket_day - date(first_last.first_commit_time) + 1 as total_days_count,
    sum(events.amount * events.amount) over (
      partition by events.event_source, events.to_artifact_id 
      order by events.bucket_day 
      rows between unbounded preceding and current row
    ) as cumulative_sum_squares
  from oso.int_events_daily__github as events
  left join oso.int_first_last_commit_to_github_repository as first_last
    on events.to_artifact_id = first_last.artifact_id
  where
    events.bucket_day between @metrics_start('DATE') and @metrics_end('DATE')
),
variance_calc as (
  select
    *,
    cumulative_sum / total_days_count as mean_activity,
    (cumulative_sum_squares - (cumulative_sum * cumulative_sum / total_days_count)) / total_days_count as variance_activity
  from activity_stats
)
select
  variance_calc.metrics_sample_date as metrics_sample_date,
  variance_calc.event_source as event_source,
  variance_calc.to_artifact_id as to_artifact_id,
  '' as from_artifact_id,
  @metric_name() as metric,
  cast(case 
    when mean_activity > 0 then variance_activity * variance_activity / mean_activity
    else -1
  end as DOUBLE) as amount
from variance_calc
