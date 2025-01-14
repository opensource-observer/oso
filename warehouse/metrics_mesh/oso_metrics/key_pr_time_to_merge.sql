select distinct
  now() as metrics_sample_date,
  event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := issue_event,
  ),
  '' as from_artifact_id,
  'PRS_TIME_TO_MERGE' as metric,
  avg(created_delta) as amount
from metrics.issue_event_time_deltas as issue_event
where event_type = 'PULL_REQUEST_MERGED'
group by 2, 3
