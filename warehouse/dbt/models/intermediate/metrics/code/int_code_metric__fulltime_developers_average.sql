with ftdevs as (
  select
    project_id,
    event_source,
    bucket_day,
    amount
  from {{ ref('int_timeseries_code_metrics__developers') }}
  where metric = 'fulltime_developers'
)

select
  ftdevs.project_id,
  ftdevs.event_source,
  time_intervals.time_interval,
  'fulltime_developer_average' as metric,
  (
    SUM(ftdevs.amount)
    / DATE_DIFF(CURRENT_DATE(), MAX(DATE(time_intervals.start_date)), day)
  ) as amount
from ftdevs
cross join {{ ref('int_time_intervals') }} as time_intervals
where
  ftdevs.bucket_day >= time_intervals.start_date
  and time_intervals.time_interval != 'ALL'
group by
  ftdevs.project_id,
  ftdevs.event_source,
  time_intervals.time_interval
