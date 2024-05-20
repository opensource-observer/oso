with all_contributions as (
  select
    project_id,
    from_artifact_id,
    event_source,
    bucket_month,
    SUM(amount) as amount
  from {{ ref('int_events_monthly_to_project') }}
  where event_type = 'COMMIT_CODE'
  group by
    project_id,
    from_artifact_id,
    event_source,
    bucket_month
),

contributions as (
  select *
  from all_contributions
  where amount < 1000 -- BOT FILTER
),

aggregated_contributions as (
  select
    contributions.project_id,
    contributions.from_artifact_id,
    contributions.event_source,
    time_intervals.time_interval,
    SUM(contributions.amount) as amount
  from contributions
  cross join {{ ref('int_time_intervals') }} as time_intervals
  where
    contributions.bucket_month
    >= TIMESTAMP_TRUNC(time_intervals.start_date, month)
  group by
    contributions.project_id,
    contributions.from_artifact_id,
    contributions.event_source,
    time_intervals.time_interval
),

ranked_contributions as (
  select
    project_id,
    event_source,
    time_interval,
    from_artifact_id,
    amount,
    RANK()
      over (
        partition by project_id, event_source, time_interval
        order by amount desc
      ) as rank,
    SUM(amount)
      over (
        partition by project_id, event_source, time_interval
      ) as total_project_amount,
    SUM(amount)
      over (
        partition by project_id, event_source, time_interval
        order by amount desc
        rows between unbounded preceding and current row
      ) as cumulative_amount
  from aggregated_contributions
)

select
  project_id,
  event_source,
  time_interval,
  'bus_factor' as metric,
  MAX(
    case
      when cumulative_amount <= total_project_amount * 0.5
        then rank
      else 1
    end
  ) as amount
from
  ranked_contributions
group by
  project_id,
  event_source,
  time_interval
