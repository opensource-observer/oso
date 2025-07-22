-- Calculate Project Velocity as a weighted combination of development activity metrics
-- Project velocity measures the number of issues, pull requests, commits, and contributors
-- Formula: Velocity Score = (w_i * I) + (w_c * C) + (w_r * R) + (w_p * P)
-- Where: I = Issues Closed, C = Commits, R = PR Reviews, P = Contributors
-- Default weights: w_i=1.0, w_c=1.0, w_r=1.0, w_p=2.0 (contributors weighted higher)
-- defined in the metrics_factories.py

with all_metrics as (
    select
        @metrics_entity_type_col('to_{entity_type}_id') as entity_id,
        @metrics_sample_date(metrics_sample_date) as metrics_sample_date,
        event_source,
        'issues_closed' as metric_type,
        amount
    from @metrics_peer_ref(closed_issues, time_aggregation := @time_aggregation)
    
    union all
    
    select
        @metrics_entity_type_col('to_{entity_type}_id') as entity_id,
        @metrics_sample_date(metrics_sample_date) as metrics_sample_date,
        event_source,
        'commits' as metric_type,
        amount
    from @metrics_peer_ref(commits, time_aggregation := @time_aggregation)
    
    union all
    
    select
        @metrics_entity_type_col('to_{entity_type}_id') as entity_id,
        @metrics_sample_date(metrics_sample_date) as metrics_sample_date,
        event_source,
        'prs_comments' as metric_type,
        amount
    from @metrics_peer_ref(prs_comments, time_aggregation := @time_aggregation)
    
    union all
    
    select
        @metrics_entity_type_col('to_{entity_type}_id') as entity_id,
        @metrics_sample_date(metrics_sample_date) as metrics_sample_date,
        event_source,
        'contributors' as metric_type,
        amount
    from @metrics_peer_ref(contributors, time_aggregation := @time_aggregation)
)

select
    metrics_sample_date,
    event_source,
    entity_id as @metrics_entity_type_col('to_{entity_type}_id'),
    '' as from_artifact_id,
    @metric_name() as metric,
    cast(
        (sum(case when metric_type = 'issues_closed' then amount else 0 end) * @weight_issues_closed) +
        (sum(case when metric_type = 'commits' then amount else 0 end) * @weight_commits) +
        (sum(case when metric_type = 'prs_comments' then amount else 0 end) * @weight_pr_reviews) +
        (sum(case when metric_type = 'contributors' then amount else 0 end) * @weight_contributors)
    as DOUBLE) as amount
from all_metrics
group by 1, 2, 3, 4, 5
