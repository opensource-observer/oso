select distinct
  now() as metrics_sample_date,
  events.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := events,
  ),
  '' as from_artifact_id,
  'GAS_FEES' as metric,
  sum(events.amount) as amount
from metrics.events_daily_to_artifact as events
where event_type = 'CONTRACT_INVOCATION_DAILY_L2_GAS_USED'
group by 2, 3
