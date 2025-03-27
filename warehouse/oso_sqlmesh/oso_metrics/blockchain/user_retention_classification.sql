with
    first_events as (
        select
            event_source,
            from_artifact_id,
            to_artifact_id,
            min(time) as first_event_date
        from oso.int_first_of_event_from_artifact
        where event_type in @activity_event_types
        group by event_source, from_artifact_id, to_artifact_id
    ),
    active_users as (
        select distinct from_artifact_id, bucket_day, event_source, to_artifact_id
        from oso.int_events_daily__blockchain
        where event_type in @activity_event_types
        where bucket_day between @metrics_start('DATE') and @metrics_end('DATE')
    )
select
    @metrics_end('DATE') as metrics_sample_date,
    active.event_source,
    @metrics_entity_type_col(
        'to_{entity_type}_id', table_alias := active, include_column_alias := true
    ),
    '' as from_artifact_id,
    @metric_name('new_users') as metric,
    count(distinct active.from_artifact_id) as amount
from active_users active
join
    first_events
    on first_events.from_artifact_id = active.from_artifact_id
    and @metrics_entity_type_col('to_{entity_type}_id', table_alias := active)
    = @metrics_entity_type_col('to_{entity_type}_id', table_alias := first_events)
where
    first_events.first_event_date
    between @metrics_start('DATE') and @metrics_end('DATE')
group by
    metrics_sample_date,
    metric,
    from_artifact_id,
    @metrics_entity_type_col('to_{entity_type}_id', table_alias := active),
    event_source
union all
select
    @metrics_end('DATE') as metrics_sample_date,
    active.event_source,
    @metrics_entity_type_col(
        'to_{entity_type}_id', table_alias := active, include_column_alias := true
    ),
    '' as from_artifact_id,
    @metric_name('returning_users') as metric,
    count(distinct active.from_artifact_id) as amount
from active_users active
join
    first_events
    on first_events.from_artifact_id = active.from_artifact_id
    and @metrics_entity_type_col('to_{entity_type}_id', table_alias := active)
    = @metrics_entity_type_col('to_{entity_type}_id', table_alias := first_events)
where first_events.first_event_date < @metrics_start('DATE')
group by
    metrics_sample_date,
    metric,
    from_artifact_id,
    @metrics_entity_type_col('to_{entity_type}_id', table_alias := active),
    event_source
