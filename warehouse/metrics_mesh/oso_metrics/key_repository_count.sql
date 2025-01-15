select distinct
  now() as metrics_sample_date,
  events.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := events,
  ),
  '' as from_artifact_id,
  'REPOSITORY_ENGAGEMENT_COUNT' as metric,
  count(distinct events.to_artifact_id) as amount
from metrics.events_daily_to_artifact as events
where events.event_type in (
  'ISSUE_OPENED',
  'STARRED',
  'PULL_REQUEST_OPENED',
  'FORKED',
  'PULL_REQUEST_REOPENED',
  'PULL_REQUEST_CLOSED',
  'COMMIT_CODE',
  'ISSUE_REOPENED',
  'PULL_REQUEST_MERGED',
  'ISSUE_CLOSED'
)
group by 2, 3
