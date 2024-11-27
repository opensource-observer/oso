with full_time_contributors as (
  with full_time_events as (
    select *
    from @metrics_peer_ref(
      developer_classifications,
      window := @rolling_window,
      unit := @rolling_unit
    )
    where metric like 'full_time%'
  )
  select
    @metrics_sample_date(full_time_events.metrics_sample_date)
      as metrics_sample_date,
    full_time_events.event_source,
    @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := full_time_events,
      include_column_alias := true
    ),
    '' as from_artifact_id,
    'full_time_contributors' as metric,
    COUNT(DISTINCT full_time_events.from_artifact_id) as amount
  from full_time_events
  group by 1, 2, 3, 4, 5
),

part_time_contributors as (
  with part_time_events as (
    select *
    from @metrics_peer_ref(
      developer_classifications,
      window := @rolling_window,
      unit := @rolling_unit
    )
    where metric like 'part_time%'
  )
  select
    @metrics_sample_date(part_time_events.metrics_sample_date)
      as metrics_sample_date,
    part_time_events.event_source,
    @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := part_time_events,
      include_column_alias := true
    ),
    '' as from_artifact_id,
    'part_time_contributors' as metric,
    COUNT(DISTINCT part_time_events.from_artifact_id) as amount
  from part_time_events
  group by 1, 2, 3, 4, 5
),

first_time_contributors as (
  select
    @metrics_sample_date(events.bucket_day) as metrics_sample_date,
    events.event_source,
    @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := events,
      include_column_alias := true
    ),
    '' as from_artifact_id,
    'first_time_contributors' as metric,
    COUNT(DISTINCT events.from_artifact_id) as amount
  from metrics.events_daily_to_artifact as events
  where events.event_type in @activity_event_types
    and events.bucket_day = @metrics_end('DATE')
    and events.from_artifact_id not in (
      select distinct from_artifact_id
      from metrics.events_daily_to_artifact
      where event_type in @activity_event_types
        and bucket_day < @metrics_end('DATE')
    )
  group by 1, 2, 3, 4, 5
),

churned_contributors as (
  select
    @metrics_end('DATE') as metrics_sample_date,
    current_period.event_source,
    @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := current_period,
      include_column_alias := true
    ),
    '' as from_artifact_id,
    'churned_contributors' as metric,
    COUNT(DISTINCT past_period.from_artifact_id) as amount
  from @metrics_peer_ref(
    developer_active_days,
    window := @rolling_window,
    unit := @rolling_unit
  ) as past_period
  left join @metrics_peer_ref(
    developer_active_days,
    window := @rolling_window,
    unit := @rolling_unit
  ) as current_period
    on past_period.from_artifact_id = current_period.from_artifact_id
    and past_period.event_source = current_period.event_source
    and @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := past_period
    ) = @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := current_period
    )
    and current_period.metrics_sample_date = @metrics_end('DATE')
  where past_period.metrics_sample_date = @relative_window_sample_date(
      @metrics_end('DATE'),
      @rolling_window,
      @rolling_unit,
      -1
    )
    and current_period.from_artifact_id is null
  group by 1, 2, 3, 4, 5
),

latest as (
  select *
  from (
    select * from full_time_contributors
    union all
    select * from part_time_contributors
    union all
    select * from first_time_contributors
    union all
    select * from churned_contributors
  ) current_month
  where metrics_sample_date = @relative_window_sample_date(
    @metrics_end('DATE'),
    1,
    'month',
    0
  )
),

previous as (
  select *
  from (
    select * from full_time_contributors
    union all
    select * from part_time_contributors
    union all
    select * from first_time_contributors
    union all
    select * from churned_contributors
  ) previous_month
  where metrics_sample_date = @relative_window_sample_date(
    @metrics_end('DATE'),
    1,
    'month',
    -1
  )
),

transitions as (
  select
    @metrics_end('DATE') as metrics_sample_date,
    coalesce(latest.event_source, previous.event_source) as event_source,
    @metrics_entity_type_alias(
      coalesce(
        @metrics_entity_type_col('to_{entity_type}_id', table_alias := latest),
        @metrics_entity_type_col('to_{entity_type}_id', table_alias := previous)
      ),
      'to_{entity_type}_id'
    ),
    '' as from_artifact_id,
    concat(
      'transition_',
      previous.metric,
      '_to_',
      latest.metric
    ) as metric,
    latest.amount - previous.amount as amount
  from previous
  left join latest 
    on latest.event_source = previous.event_source
    and @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := latest
    ) = @metrics_entity_type_col(
      'to_{entity_type}_id',
      table_alias := previous
    )
  where (
      previous.metric = 'full_time_contributors'
      and latest.metric = 'part_time_contributors'
    )
    or (
      previous.metric = 'part_time_contributors'
      and latest.metric = 'full_time_contributors'
    )
    or (
      previous.metric = 'churned_contributors'
      and latest.metric in ('full_time_contributors', 'part_time_contributors')
    )
    or (
      previous.metric in ('full_time_contributors', 'part_time_contributors')
      and latest.metric = 'churned_contributors'
    )
)

select * from transitions
