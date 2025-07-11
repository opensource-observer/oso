-- Calculate Self Merge Rates: no_of_self_merged_prs_without_comments / no_of_merged_prs
-- Self-merged PRs are PRs where the author is the same as the merger and have no comments
with pr_events as (
  select
    @metrics_sample_date(events.time) as metrics_sample_date,
    events.event_source,
    events.to_artifact_id,
    events.from_artifact_id,
    events.pr_id,
    events.pr_number,
    events.merged_at,
    events.comments,
    events.event_type
  from oso.int_events_aux_prs as events
  where
    events.time between @metrics_start('DATE') and @metrics_end('DATE')
),
merged_prs as (
  select
    metrics_sample_date,
    event_source,
    to_artifact_id,
    pr_id,
    pr_number,
    max(merged_at) as merged_at,
    max(comments) as comments,
    -- Get both the PR author (from PULL_REQUEST events) and merger (from PULL_REQUEST_MERGED events)
    max(case when event_type = 'PULL_REQUEST_OPENED' then from_artifact_id end) as pr_author_id,
    max(case when event_type = 'PULL_REQUEST_MERGED' then from_artifact_id end) as pr_merger_id
  from pr_events
  group by
    metrics_sample_date,
    event_source,
    to_artifact_id,
    pr_id,
    pr_number
  having max(merged_at) is not null
),
self_merged_prs_without_comments as (
  select
    metrics_sample_date,
    event_source,
    to_artifact_id,
    count(*) as self_merged_count
  from merged_prs
  where
    comments = 0
    and pr_author_id = pr_merger_id
  group by
    metrics_sample_date,
    event_source,
    to_artifact_id
),
total_merged_prs as (
  select
    metrics_sample_date,
    event_source,
    to_artifact_id,
    count(*) as total_merged_count
  from merged_prs
  group by
    metrics_sample_date,
    event_source,
    to_artifact_id
)
select
  total.metrics_sample_date as metrics_sample_date,
  total.event_source as event_source,
  total.to_artifact_id as to_artifact_id,
  '' as from_artifact_id,
  @metric_name() as metric,
  cast(case 
    when total.total_merged_count > 0 then 
      coalesce(self_merged.self_merged_count, 0) / cast(total.total_merged_count as double)
    else NULL
  end as double) as amount
from total_merged_prs as total
left join self_merged_prs_without_comments as self_merged
  on total.metrics_sample_date = self_merged.metrics_sample_date
  and total.event_source = self_merged.event_source
  and total.to_artifact_id = self_merged.to_artifact_id
