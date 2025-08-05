-- Calculate Fano Factor (variance²/mean) as a measure of burstiness for repository activity
-- Since the rows are not zero-filled, we need to calculate using manual formulas instead
-- of using built in VAR_POP and AVG functions.
-- Breakdown of formulas:
-- Average = SUM/COUNT
-- VAR_POP = Σ((amount-mean)²)/COUNT
--         = Σ(amount² - 2*amount*mean + mean²)/COUNT
--         = Σ(amount²)/COUNT - Σ(2*amount*mean)/COUNT + Σ(mean²)/COUNT
--         = Σ(amount²)/COUNT - -2*mean * Σ(amount)/COUNT + COUNT * mean² / COUNT
--         = Σ(amount²)/COUNT - 2*mean² + mean²
--         = Σ(amount²)/COUNT - mean²
with daily_total as (
  select
    bucket_day,
    to_artifact_id::VARCHAR AS to_artifact_id,
    event_source::VARCHAR,
    SUM(amount::DOUBLE)::DOUBLE AS amount
  from oso.int_events_daily__github as events
  where events.bucket_day BETWEEN @metrics_start('DATE') AND @metrics_end('DATE')
  group by
    bucket_day,
    to_artifact_id,
    event_source
),
activity_stats as (
  select
    @metrics_sample_date(events.bucket_day) as metrics_sample_date,
    events.event_source,
    events.to_artifact_id,
    events.amount,
    date_diff('day', date(first_last.first_commit_time), events.bucket_day) + 1 as total_days_count,
    sum(events.amount) over w as cumulative_sum,
    sum(events.amount * events.amount) over w as cumulative_sum_squares,
    count(*) over w as actual_days_count
  from daily_total as events
  left join oso.int_first_last_commit_to_github_repository as first_last
    on events.to_artifact_id = first_last.artifact_id
  window w as (
    partition by events.event_source, events.to_artifact_id
    order by events.bucket_day
    rows between unbounded preceding and current row
  )
  where
    events.bucket_day between @metrics_start('DATE') and @metrics_end('DATE')
),
variance_calc as (
  select
    *,
    cast(cumulative_sum as DOUBLE) / cast(total_days_count as DOUBLE) as mean_activity,
    cast(cumulative_sum_squares as DOUBLE) / cast(total_days_count as DOUBLE) -
    power(cast(cumulative_sum as DOUBLE) / cast(total_days_count as DOUBLE), 2) as variance_activity
  from activity_stats
)
select
  variance_calc.metrics_sample_date,
  variance_calc.event_source,
  variance_calc.to_artifact_id,
  '' as from_artifact_id,
  @metric_name() as metric,
  cast(case
    when sum(mean_activity) > 0 then sum(variance_activity * variance_activity) / sum(mean_activity)
    else NULL
  end as DOUBLE) as amount
from variance_calc
group by 1, 2, 3, 4, 5
