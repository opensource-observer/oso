with first_events as (
  select 
    from_artifact_id,
    min(time::date) as first_event_date
  from @first_of_event_from_artifact
  where event_type in (@activity_event_types)
  group by from_artifact_id
),
active_users as (
  select distinct
    from_artifact_id,
    event_date,
    event_source,
    @metrics_entity_type_col(
      'to_{entity_type}_id',
      include_column_alias := true
    )
  from @metrics_source(
    event_types := @activity_event_types
  )
  where event_date >= @metrics_start('DATE')
)

select 
  @metrics_end('DATE') as metrics_sample_date,
  active.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := active,
    include_column_alias := true
  ),
  '' as from_artifact_id,
  @metric_name('new_users') as metric,
  COUNT(DISTINCT active.from_artifact_id) as amount
from active_users active
join first_events on first_events.from_artifact_id = active.from_artifact_id
where first_events.first_event_date >= @metrics_start('DATE')
group by 
  metrics_sample_date,
  metric,
  from_artifact_id,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := active
  ),
  event_source

union all

select 
  @metrics_end('DATE') as metrics_sample_date,
  active.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := active,
    include_column_alias := true
  ),
  '' as from_artifact_id,
  @metric_name('returning_users') as metric,
  COUNT(DISTINCT active.from_artifact_id) as amount
from active_users active
join first_events on first_events.from_artifact_id = active.from_artifact_id
where first_events.first_event_date < @metrics_start('DATE')
group by 
  metrics_sample_date,
  metric,
  from_artifact_id,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := active
  ),
  event_source
