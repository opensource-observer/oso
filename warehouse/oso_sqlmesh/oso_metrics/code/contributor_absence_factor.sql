-- Contributor Absence Factor (previously known as Bus Factor)
-- Calculates the minimum number of contributors responsible for 50% of total contributions
-- A lower value indicates higher risk if those contributors leave
-- https://chaoss.community/kb/metric-contributor-absence-factor/

with contributor_contributions as (
  select
    @metrics_sample_date(events.bucket_day) as metrics_sample_date,
    events.event_source,
    events.to_artifact_id,
    events.from_artifact_id,
    sum(events.amount) as contribution_amount
  from oso.int_events_daily__github as events
  where
    events.bucket_day between @metrics_start('DATE') and @metrics_end('DATE')
  group by 1, 2, 3, 4
),

total_contributions as (
  select
    metrics_sample_date,
    event_source,
    to_artifact_id,
    sum(contribution_amount) as total_amount
  from contributor_contributions
  group by 1, 2, 3
),

ranked_contributors as (
  select
    cc.metrics_sample_date,
    cc.event_source,
    cc.to_artifact_id,
    cc.from_artifact_id,
    cc.contribution_amount,
    tc.total_amount,
    row_number() over (
      partition by cc.metrics_sample_date, cc.event_source, cc.to_artifact_id 
      order by cc.contribution_amount desc
    ) as contributor_rank
  from contributor_contributions cc
  inner join total_contributions tc
    on cc.metrics_sample_date = tc.metrics_sample_date
    and cc.event_source = tc.event_source
    and cc.to_artifact_id = tc.to_artifact_id
),

cumulative_contributions as (
  select
    metrics_sample_date,
    event_source,
    to_artifact_id,
    from_artifact_id,
    contribution_amount,
    total_amount,
    contributor_rank,
    sum(contribution_amount) over (
      partition by metrics_sample_date, event_source, to_artifact_id 
      order by contributor_rank
      rows unbounded preceding
    ) as cumulative_amount
  from ranked_contributors
),

absence_factor as (
  select
    metrics_sample_date,
    event_source,
    to_artifact_id,
    min(contributor_rank) as contributor_absence_factor
  from cumulative_contributions
  where cumulative_amount >= (total_amount * 0.5)
  group by 1, 2, 3
)

select
  af.metrics_sample_date,
  af.event_source,
  af.to_artifact_id,
  '' as from_artifact_id,
  @metric_name() as metric,
  af.contributor_absence_factor as amount
from absence_factor af
