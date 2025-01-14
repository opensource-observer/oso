select distinct
  now() as metrics_sample_date,
  events.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := events,
  ),
  '' as from_artifact_id,
  'LAST_COMMIT' as metric,
  @str_to_unix_timestamp(
    split_part(
      cast(max(bucket_day) as string), ' ', 1
    )
  ) as amount
from metrics.events_daily_to_artifact as events
where event_type = 'COMMIT_CODE'
group by 2, 3
