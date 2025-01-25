MODEL (
  name metrics.int_developers_by_project,
  description 'Relationships between developers and projects (by commits)',
  kind FULL,
);


select
  events.from_artifact_id as developer_artifact_id,
  events.to_artifact_id,
  events.project_id,
  repositories.language,
  min(events.bucket_day) as first_contribution_time,
  max(events.bucket_day) as last_contribution_time,
  count(distinct events.bucket_day) as num_days_contributed,
  sum(events.amount) as num_commits
from metrics.int_events_daily_to_project as events
join metrics.int_repositories as repositories
  on events.to_artifact_id = repositories.artifact_id
where events.event_type = 'COMMIT_CODE'
group by 1,2,3,4
