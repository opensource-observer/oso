with
    -- Get the first contribution date for each contributor to the entity
    first_contribution_to_entity as (
        select
            from_artifact_id,
            event_source,
            @metrics_entity_type_col(
                'to_{entity_type}_id',
                table_alias := first_contribution,
                include_column_alias := true
            ),
            @metrics_sample_date("time") as first_contribution_date
        from
            @metrics_entity_type_table(
                'oso.int_first_contribution_to_{entity_type}'
            ) as first_contribution
    ),
    -- Get current month activity for each contributor
    current_month_activity as (
        select
            active.metrics_sample_date,
            active.event_source,
            active.from_artifact_id,
            @metrics_entity_type_col(
                'to_{entity_type}_id',
                table_alias := active,
                include_column_alias := true
            ),
            active.amount as active_days,
            -- Classify activity level
            case
                when active.amount / @metrics_sample_interval_length(active.metrics_sample_date, 'day') >= @full_time_ratio
                then 'full_time'
                else 'part_time'
            end as activity_level
        from
            @metrics_peer_ref(
                contributor_active_days,
                time_aggregation := @time_aggregation,
            ) as active
    ),
    -- Join activity with first contribution dates and get previous period's activity
    contributor_with_history as (
        select
            curr.metrics_sample_date,
            curr.event_source,
            curr.from_artifact_id,
            @metrics_entity_type_col(
                'to_{entity_type}_id',
                table_alias := curr,
                include_column_alias := true
            ),
            curr.activity_level,
            first_contrib.first_contribution_date,
            -- Get previous period's activity date using LAG
            lag(curr.metrics_sample_date) over (
                partition by
                    @metrics_entity_type_col('to_{entity_type}_id', table_alias := curr),
                    curr.from_artifact_id,
                    curr.event_source
                order by curr.metrics_sample_date
            ) as prev_contribution_date,
            -- Get previous period's activity level using LAG
            lag(curr.activity_level) over (
                partition by
                    @metrics_entity_type_col('to_{entity_type}_id', table_alias := curr),
                    curr.from_artifact_id,
                    curr.event_source
                order by curr.metrics_sample_date
            ) as prev_activity_level
        from current_month_activity as curr
        left join first_contribution_to_entity as first_contrib
            on curr.from_artifact_id = first_contrib.from_artifact_id
            and curr.event_source = first_contrib.event_source
            and @metrics_entity_type_col('to_{entity_type}_id', table_alias := curr)
                = @metrics_entity_type_col('to_{entity_type}_id', table_alias := first_contrib)
    ),
    -- Calculate expected previous period for gap detection and look ahead for next period
    contributor_with_expected_dates as (
        select
            cwh.*,
            -- Calculate what the immediate previous period SHOULD be
            case @time_aggregation
                when 'monthly' then date_add('month', -1, cwh.metrics_sample_date)
                when 'yearly' then date_add('year', -1, cwh.metrics_sample_date)
            end as expected_prev_date,
            -- Look ahead to see if they're active in the next period
            lead(cwh.metrics_sample_date) over (
                partition by
                    @metrics_entity_type_col('to_{entity_type}_id', table_alias := cwh),
                    cwh.from_artifact_id,
                    cwh.event_source
                order by cwh.metrics_sample_date
            ) as next_contribution_date,
            -- Calculate what the immediate next period SHOULD be
            case @time_aggregation
                when 'monthly' then date_add('month', 1, cwh.metrics_sample_date)
                when 'yearly' then date_add('year', 1, cwh.metrics_sample_date)
            end as expected_next_date
        from contributor_with_history as cwh
    ),
    contributor_with_expected_prev as (
        select * from contributor_with_expected_dates
    ),
    -- Classify contributors based on their state
    contributor_classifications as (
        select
            cwep.metrics_sample_date,
            cwep.event_source,
            cwep.from_artifact_id,
            @metrics_entity_type_col(
                'to_{entity_type}_id',
                table_alias := cwep,
                include_column_alias := true
            ),
            cwep.activity_level,
            -- Determine contributor classification
            case
                -- First-time contributor: first contribution date equals current period
                when cwep.first_contribution_date = cwep.metrics_sample_date
                    then 'first_time_contributor'
                -- New part-time contributor: was first-time last period, now part-time
                when cwep.first_contribution_date = cwep.prev_contribution_date
                    and cwep.prev_contribution_date = cwep.expected_prev_date
                    and cwep.activity_level = 'part_time'
                    then 'new_part_time_contributor'
                -- New full-time contributor: was first-time last period, now full-time
                when cwep.first_contribution_date = cwep.prev_contribution_date
                    and cwep.prev_contribution_date = cwep.expected_prev_date
                    and cwep.activity_level = 'full_time'
                    then 'new_full_time_contributor'
                -- Active part-time contributor: was part-time last period, still part-time
                when cwep.prev_contribution_date = cwep.expected_prev_date
                    and cwep.prev_activity_level = 'part_time'
                    and cwep.activity_level = 'part_time'
                    then 'active_part_time_contributor'
                -- Active full-time contributor: was full-time last period, still full-time
                when cwep.prev_contribution_date = cwep.expected_prev_date
                    and cwep.prev_activity_level = 'full_time'
                    and cwep.activity_level = 'full_time'
                    then 'active_full_time_contributor'
                -- Part-time to full-time contributor: was part-time last period, now full-time
                when cwep.prev_contribution_date = cwep.expected_prev_date
                    and cwep.prev_activity_level = 'part_time'
                    and cwep.activity_level = 'full_time'
                    then 'part_time_to_full_time_contributor'
                -- Full-time to part-time contributor: was full-time last period, now part-time
                when cwep.prev_contribution_date = cwep.expected_prev_date
                    and cwep.prev_activity_level = 'full_time'
                    and cwep.activity_level = 'part_time'
                    then 'full_time_to_part_time_contributor'
                -- Reactivated part-time contributor: had activity before but not in immediate previous period, now part-time
                when cwep.prev_contribution_date is not null
                    and cwep.prev_contribution_date < cwep.expected_prev_date
                    and cwep.activity_level = 'part_time'
                    then 'reactivated_part_time_contributor'
                -- Reactivated full-time contributor: had activity before but not in immediate previous period, now full-time
                when cwep.prev_contribution_date is not null
                    and cwep.prev_contribution_date < cwep.expected_prev_date
                    and cwep.activity_level = 'full_time'
                    then 'reactivated_full_time_contributor'
            end as contributor_label
        from contributor_with_expected_prev as cwep
    ),
    -- Detect churned contributors by looking for gaps in the next period
    churned_contributors as (
        select
            cwep.expected_next_date as metrics_sample_date,
            cwep.event_source,
            cwep.from_artifact_id,
            @metrics_entity_type_col(
                'to_{entity_type}_id',
                table_alias := cwep,
                include_column_alias := true
            ),
            -- Determine churn classification based on last known state
            case
                -- Churned after first-time: first contribution was in the last period and now they're gone
                when cwep.first_contribution_date = cwep.metrics_sample_date
                    then 'churned_after_first_time_contributor'
                -- Churned after part-time: was part-time in the last period
                when cwep.activity_level = 'part_time'
                    then 'churned_after_part_time_contributor'
                -- Churned after full-time: was full-time in the last period
                when cwep.activity_level = 'full_time'
                    then 'churned_after_full_time_contributor'
            end as contributor_label
        from contributor_with_expected_prev as cwep
        where (
            -- Either no next contribution, or there's a gap
            cwep.next_contribution_date is null
            or cwep.next_contribution_date > cwep.expected_next_date
        )
        and cwep.expected_next_date <= @metrics_end('DATE')  -- Only churn events within date range
    ),
    -- Combine active and churned contributors
    all_contributor_states as (
        select
            cc.metrics_sample_date,
            cc.event_source,
            @metrics_entity_type_col(
                'to_{entity_type}_id',
                table_alias := cc,
                include_column_alias := true
            ),
            cc.from_artifact_id,
            cc.contributor_label
        from contributor_classifications as cc
        where cc.contributor_label is not null
        union all
        select
            churned.metrics_sample_date,
            churned.event_source,
            @metrics_entity_type_col(
                'to_{entity_type}_id',
                table_alias := churned,
                include_column_alias := true
            ),
            churned.from_artifact_id,
            churned.contributor_label
        from churned_contributors as churned
    )
-- Count contributors by classification
select
    acs.metrics_sample_date,
    acs.event_source,
    @metrics_entity_type_col(
        'to_{entity_type}_id',
        table_alias := acs,
        include_column_alias := true
    ),
    '' as from_artifact_id,
    @metric_name(acs.contributor_label) as metric,
    count(distinct acs.from_artifact_id) as amount
from all_contributor_states as acs
group by
    acs.metrics_sample_date,
    acs.event_source,
    @metrics_entity_type_col('to_{entity_type}_id', table_alias := acs),
    acs.contributor_label
