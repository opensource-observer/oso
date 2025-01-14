select distinct
  now() as metrics_sample_date,
  events.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := events,
  ),
  '' as from_artifact_id,
  'ACTIVE_CONTRACTS' as metric,
  count(distinct events.to_artifact_id) as amount
from metrics.events_daily_to_artifact as events
where events.event_type = 'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT'
group by 2, 3
