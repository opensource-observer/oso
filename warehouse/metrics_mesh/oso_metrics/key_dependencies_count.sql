select distinct
  now() as metrics_sample_date,
  events.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := events,
  ),
  '' as from_artifact_id,
  'DEPENDENCY_COUNT' as metric,
  count(distinct events.from_artifact_id) as amount
from metrics.events_daily_to_artifact as events
where event_type = 'ADD_DEPENDENCY'
group by 2, 3
