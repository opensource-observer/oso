with
    first_of_activity_to_entity as (
        -- We use this CTE to get the first of a specific type of event to a specific
        -- entity.
        -- select MIN(time) as `time`,
        -- event_source,
        -- from_artifact_id,
        -- to_artifact_id
        -- from oso.int_first_of_event_from_artifact
        -- where event_type in @activity_event_types
        -- group by event_source,
        -- from_artifact_id,
        -- to_artifact_id
        select
            `time`,
            event_source,
            from_artifact_id,
            @metrics_entity_type_col(
                'to_{entity_type}_id',
                table_alias := first_contribution,
                include_column_alias := true
            )
        from
            @metrics_entity_type_table(
                'oso.int_first_contribution_to_{entity_type}'
            ) as first_contribution
    ),
    filtered_first_of as (
        -- Filtered first of events to just the current period we are measuring.
        select distinct
            event_source,
            from_artifact_id,
            @metrics_entity_type_col(
                'to_{entity_type}_id', table_alias := fo, include_column_alias := true
            )
        from first_of_activity_to_entity as fo
        where `time` between @metrics_start('DATE') and @metrics_end('DATE')
    ),
    new_contributors as (
        -- Only new contributors. we do this by joining on the filtered first of events
        -- in this time range
        select
            active.metrics_sample_date,
            active.event_source,
            @metrics_entity_type_col(
                'to_{entity_type}_id',
                table_alias := active,
                include_column_alias := true,
            ),
            @metric_name('new_contributors') as metric,
            count(distinct active.from_artifact_id) as amount
        from
            @metrics_peer_ref(
                contributor_active_days,
                window := @rolling_window, unit := @rolling_unit
            ) as active
        inner join
            filtered_first_of as ffo
            on active.from_artifact_id = ffo.from_artifact_id
            and active.event_source = ffo.event_source
            and @metrics_entity_type_col('to_{entity_type}_id', table_alias := active)
            = @metrics_entity_type_col('to_{entity_type}_id', table_alias := ffo)
        where active.metrics_sample_date = @metrics_end('DATE')
        group by
            metric,
            @metrics_entity_type_col('to_{entity_type}_id', table_alias := active),
            active.event_source,
            active.metrics_sample_date
    ),
    lag_events_filtered as (
        -- This filters for lagged events of the activity types we care about
        select
            events.bucket_day,
            events.event_source,
            events.from_artifact_id,
            events.to_artifact_id,
            max(last_event) as last_event
        from oso.int_events_daily_to_artifact_with_lag as events
        where event_type in @activity_event_types
        group by bucket_day, event_source, from_artifact_id, to_artifact_id
    ),
    contributors_earliest_event_in_period as (
        -- This uses a window function to get the earliest event in a given period for
        -- a specific contributor. We then use the "last_event" value of this to
        -- determine the resurrection status.
        select
            events.bucket_day,
            events.event_source,
            events.from_artifact_id,
            @metrics_entity_type_col(
                'to_{entity_type}_id',
                table_alias := events,
                include_column_alias := true,
            ),
            events.last_event,
            row_number() over (
                partition by
                    @metrics_entity_type_col(
                        'to_{entity_type}_id', table_alias := events
                    ),
                    events.from_artifact_id,
                    events.event_source,
                order by bucket_day asc
            ) as event_rank
        from lag_events_filtered as events
    ),
    contributors_last_event as (
        -- Gets the resurrected contributors based on the date of the last event.
        select
            events.event_source,
            events.from_artifact_id,
            @metrics_entity_type_col(
                'to_{entity_type}_id',
                table_alias := events,
                include_column_alias := true,
            ),
            case
                when count(events.last_event) < count(*)
                then null
                else max(events.last_event)
            end as last_event
        from contributors_earliest_event_in_period as events
        where event_rank = 1
        group by
            events.from_artifact_id,
            @metrics_entity_type_col('to_{entity_type}_id', table_alias := events,),
            events.event_source
    ),
    resurrected_contributors as (
        -- resurrected users are users that had previously churned or went dormant for
        -- at least one period but have returned
        select
            active.metrics_sample_date,
            active.event_source,
            @metrics_entity_type_col(
                'to_{entity_type}_id',
                table_alias := active,
                include_column_alias := true,
            ),
            @metric_name('resurrected_contributors') as metric,
            count(distinct active.from_artifact_id) as amount
        from
            @metrics_peer_ref(
                contributor_active_days,
                window := @rolling_window, unit := @rolling_unit
            ) as active
        inner join
            contributors_last_event as last_event
            on active.from_artifact_id = last_event.from_artifact_id
            and active.event_source = last_event.event_source
            and @metrics_entity_type_col('to_{entity_type}_id', table_alias := active)
            = @metrics_entity_type_col('to_{entity_type}_id', table_alias := last_event)
        where
            active.metrics_sample_date = @metrics_end('DATE')
            and last_event.last_event is not null
            and last_event.last_event
            <= @metrics_start('DATE') - interval @rolling_window day
        group by
            metric,
            @metrics_entity_type_col('to_{entity_type}_id', table_alias := active),
            active.event_source,
            active.metrics_sample_date
    )
select
    active.metrics_sample_date,
    active.event_source,
    @metrics_entity_type_col(
        'to_{entity_type}_id', table_alias := active, include_column_alias := true,
    ),
    '' as from_artifact_id,
    @metric_name('full_time_contributors') as metric,
    count(distinct active.from_artifact_id) as amount
from
    @metrics_peer_ref(
        contributor_active_days, window := @rolling_window, unit := @rolling_unit
    ) as active
where
    active.amount / @rolling_window >= @full_time_ratio
    and active.metrics_sample_date = @metrics_end('DATE')
group by
    metric,
    from_artifact_id,
    @metrics_entity_type_col('to_{entity_type}_id', table_alias := active,),
    event_source,
    metrics_sample_date
union all
select
    active.metrics_sample_date,
    active.event_source,
    @metrics_entity_type_col(
        'to_{entity_type}_id', table_alias := active, include_column_alias := true,
    ),
    '' as from_artifact_id,
    @metric_name('part_time_contributors') as metric,
    count(distinct active.from_artifact_id) as amount
from
    @metrics_peer_ref(
        contributor_active_days, window := @rolling_window, unit := @rolling_unit
    ) as active
where
    active.amount / @rolling_window < @full_time_ratio
    and active.metrics_sample_date = @metrics_end('DATE')
group by
    metric,
    from_artifact_id,
    @metrics_entity_type_col('to_{entity_type}_id', table_alias := active),
    active.event_source,
    active.metrics_sample_date
union all
select
    new.metrics_sample_date,
    new.event_source,
    @metrics_entity_type_col(
        'to_{entity_type}_id', table_alias := new, include_column_alias := true,
    ),
    '' as from_artifact_id,
    new.metric,
    new.amount as amount
from new_contributors as new
union all
select
    resurrected.metrics_sample_date,
    resurrected.event_source,
    @metrics_entity_type_col(
        'to_{entity_type}_id', table_alias := resurrected, include_column_alias := true,
    ),
    '' as from_artifact_id,
    resurrected.metric,
    resurrected.amount as amount
from resurrected_contributors as resurrected
union all
-- All active contributors
select
    active.metrics_sample_date,
    active.event_source,
    @metrics_entity_type_col(
        'to_{entity_type}_id', table_alias := active, include_column_alias := true,
    ),
    '' as from_artifact_id,
    @metric_name('active_contributors') as metric,
    count(distinct active.from_artifact_id) as amount
from
    @metrics_peer_ref(
        contributor_active_days, window := @rolling_window, unit := @rolling_unit
    ) as active
where active.metrics_sample_date = @metrics_end('DATE')
group by
    metric,
    from_artifact_id,
    @metrics_entity_type_col('to_{entity_type}_id', table_alias := active),
    event_source,
    metrics_sample_date
