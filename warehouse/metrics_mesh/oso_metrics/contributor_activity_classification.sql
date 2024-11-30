with first_of_activity_to_entity as (
  -- We use this CTE to get the first of a specific type of event to a specific
  -- entity.
  select MIN(time) as `time`,
    event_source,
    from_artifact_id,
    to_artifact_id
  from metrics.first_of_event_from_artifact
  where event_type in @activity_event_types
  group by event_source,
    from_artifact_id,
    to_artifact_id
),
filtered_first_of as (
  -- Filtered first of events to just the current period we are measuring.
  select distinct event_source,
    from_artifact_id,
    @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := fo,
      include_column_alias := true
    )
  from first_of_activity_to_entity as fo
  where `time` between @metrics_start('DATE') and @metrics_end('DATE')
),
new_contributors as (
  -- Only new contributors. we do this by joining on the filtered first of events
  -- in this time range
  select active.metrics_sample_date,
    active.event_source,
    @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := active,
      include_column_alias := true,
    ),
    @metric_name('new_contributors') as metric,
    COUNT(DISTINCT active.from_artifact_id) as amount
  from @metrics_peer_ref(
      contributor_active_days,
      window := @rolling_window,
      unit := @rolling_unit
    ) as active
    inner join filtered_first_of as ffo on active.from_artifact_id = ffo.from_artifact_id
    and active.event_source = ffo.event_source
    and @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := active
    ) = @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := ffo
    )
  where active.metrics_sample_date = @metrics_end('DATE')
  group by metric,
    @metrics_entity_type_col('to_{entity_type}_id', table_alias := active),
    active.event_source,
    active.metrics_sample_date
)
select active.metrics_sample_date,
  active.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := active,
    include_column_alias := true,
  ),
  '' as from_artifact_id,
  @metric_name('full_time_contributors') as metric,
  COUNT(DISTINCT active.from_artifact_id) as amount
from @metrics_peer_ref(
    contributor_active_days,
    window := @rolling_window,
    unit := @rolling_unit
  ) as active
where active.amount / @rolling_window >= @full_time_ratio
  and active.metrics_sample_date = @metrics_end('DATE')
group by metric,
  from_artifact_id,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := active,
  ),
  event_source,
  metrics_sample_date
union all
select active.metrics_sample_date,
  active.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := active,
    include_column_alias := true,
  ),
  '' as from_artifact_id,
  @metric_name('part_time_contributors') as metric,
  COUNT(DISTINCT active.from_artifact_id) as amount
from @metrics_peer_ref(
    contributor_active_days,
    window := @rolling_window,
    unit := @rolling_unit
  ) as active
where active.amount / @rolling_window < @full_time_ratio
  and active.metrics_sample_date = @metrics_end('DATE')
group by metric,
  from_artifact_id,
  @metrics_entity_type_col('to_{entity_type}_id', table_alias := active),
  active.event_source,
  active.metrics_sample_date
union all
select new.metrics_sample_date,
  new.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := new,
    include_column_alias := true,
  ),
  '' as from_artifact_id,
  new.metric,
  new.amount as amount
from new_contributors as new
union all
-- All active contributors
select active.metrics_sample_date,
  active.event_source,
  @metrics_entity_type_col(
    'to_{entity_type}_id',
    table_alias := active,
    include_column_alias := true,
  ),
  '' as from_artifact_id,
  @metric_name('active_contributors') as metric,
  COUNT(DISTINCT active.from_artifact_id) as amount
from @metrics_peer_ref(
    contributor_active_days,
    window := @rolling_window,
    unit := @rolling_unit
  ) as active
where active.metrics_sample_date = @metrics_end('DATE')
group by metric,
  from_artifact_id,
  @metrics_entity_type_col('to_{entity_type}_id', table_alias := active),
  event_source,
  metrics_sample_date