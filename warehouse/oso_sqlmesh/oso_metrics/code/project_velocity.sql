-- Calculate Project Velocity as a weighted combination of development activity metrics
-- Project velocity measures the number of issues, pull requests, commits, and contributors
-- Formula: Velocity Score = (w_i * I) + (w_c * C) + (w_r * R) + (w_p * P)
-- Where: I = Issues Closed, C = Commits, R = PR Reviews, P = Contributors
-- Default weights: w_i=1.0, w_c=1.0, w_r=1.0, w_p=2.0 (contributors weighted higher)
-- defined in the metrics_factories.py

with issues_closed as (
    select
        @metrics_entity_type_col(
            'to_{entity_type}_id',
        ),
        @metrics_sample_date(metrics_sample_date) as metrics_sample_date,
        event_source as event_source,
        amount as issues_closed_count
    from @metrics_peer_ref(
        closed_issues,
        time_aggregation := @time_aggregation
    )
),
commits as (
    select
        @metrics_entity_type_col(
            'to_{entity_type}_id',
        ),
        @metrics_sample_date(metrics_sample_date) as metrics_sample_date,
        event_source as event_source,
        amount as commits_count
    from @metrics_peer_ref(
        commits,
        time_aggregation := @time_aggregation
    )
),
prs_comments as (
    select
        @metrics_entity_type_col(
            'to_{entity_type}_id',
        ),
        @metrics_sample_date(metrics_sample_date) as metrics_sample_date,
        event_source as event_source,
        amount as prs_comments_count
    from @metrics_peer_ref(
        prs_comments,
        time_aggregation := @time_aggregation
    )
),
contributors as (
    select
        @metrics_entity_type_col(
            'to_{entity_type}_id',
        ),
        @metrics_sample_date(metrics_sample_date) as metrics_sample_date,
        event_source as event_source,
        amount as contributors_count
    from @metrics_peer_ref(
        contributors,
        time_aggregation := @time_aggregation
    )
),
all_dates_entities as (
    select distinct
        metrics_sample_date,
        event_source,
        @metrics_entity_type_col(
            'to_{entity_type}_id',
        )
    from (
        select metrics_sample_date, event_source, @metrics_entity_type_col('to_{entity_type}_id') from issues_closed
        union
        select metrics_sample_date, event_source, @metrics_entity_type_col('to_{entity_type}_id') from commits
        union
        select metrics_sample_date, event_source, @metrics_entity_type_col('to_{entity_type}_id') from prs_comments 
        union
        select metrics_sample_date, event_source, @metrics_entity_type_col('to_{entity_type}_id') from contributors
    )
)

select
    ade.metrics_sample_date,
    ade.event_source,
    @metrics_entity_type_col(
        'to_{entity_type}_id',
        table_alias := ade,
    ) as @metrics_entity_type_col(
        'to_{entity_type}_id',
    ),
    '' as from_artifact_id,
    @metric_name() as metric,
    cast(
        (coalesce(ic.issues_closed_count, 0) * @weight_issues_closed) +
        (coalesce(c.commits_count, 0) * @weight_commits) +
        (coalesce(pr.prs_comments_count, 0) * @weight_pr_reviews) +
        (coalesce(cont.contributors_count, 0) * @weight_contributors)
    as DOUBLE) as amount
from all_dates_entities as ade
left join issues_closed as ic 
    on ade.metrics_sample_date = ic.metrics_sample_date
    and ade.event_source = ic.event_source
    and @metrics_entity_type_col(
        'to_{entity_type}_id',
        table_alias := ade,
    ) = @metrics_entity_type_col(
        'to_{entity_type}_id',
        table_alias := ic,
    )
left join commits as c
    on ade.metrics_sample_date = c.metrics_sample_date
    and ade.event_source = c.event_source
    and @metrics_entity_type_col(
        'to_{entity_type}_id',
        table_alias := ade,
    ) = @metrics_entity_type_col(
        'to_{entity_type}_id',
        table_alias := c,
    )
left join prs_comments as pr
    on ade.metrics_sample_date = pr.metrics_sample_date
    and ade.event_source = pr.event_source
    and @metrics_entity_type_col(
        'to_{entity_type}_id',
        table_alias := ade,
    ) = @metrics_entity_type_col(
        'to_{entity_type}_id',
        table_alias := pr,
    )
left join contributors as cont
    on ade.metrics_sample_date = cont.metrics_sample_date
    and ade.event_source = cont.event_source
    and @metrics_entity_type_col(
        'to_{entity_type}_id',
        table_alias := ade,
    ) = @metrics_entity_type_col(
        'to_{entity_type}_id',
        table_alias := cont,
    )
