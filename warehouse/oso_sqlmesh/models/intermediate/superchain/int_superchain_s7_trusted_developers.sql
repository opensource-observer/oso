model(
    name oso.int_superchain_s7_trusted_developers,
    description "Identifies trusted developers based on commit history to relevant onchain builder repositories",
    kind incremental_by_time_range(
        time_column sample_date, batch_size 90, batch_concurrency 1, lookback 7
    ),
    start '2015-01-01',
    cron '@daily',
    partitioned_by day("sample_date"),
    grain(sample_date, project_id, developer_id)
)
;

@def(min_repo_stars, 5)
;
@def(last_repo_update_date, '2024-07-01')
;
@def(active_months_threshold, 3)
;
@def(commits_threshold, 20)
;
@def(last_commit_threshold_months, 12)
;

with
    eligible_onchain_builder_repos as (
        select
            repos.artifact_id as repo_artifact_id,
            repos.project_id,
            cast(builders.sample_date as timestamp) as sample_date
        from oso.int_repositories_enriched as repos
        inner join
            oso.int_superchain_s7_onchain_builder_eligibility as builders
            on repos.project_id = builders.project_id
        where
            repos.language in ('TypeScript', 'Solidity', 'Rust')
            and repos.updated_at > cast(@last_repo_update_date as timestamp)
            and repos.star_count > @min_repo_stars
            and builders.is_eligible
            and builders.sample_date between @start_dt and @end_dt
    ),

    developer_activity as (
        select
            repos.project_id,
            repos.sample_date,
            events.developer_id,
            events.developer_name,
            sum(events.total_events) as total_commits_to_project,
            min(events.first_event) as first_commit,
            max(events.last_event) as last_commit
        from oso.int_developer_activity_by_repo as events
        inner join
            eligible_onchain_builder_repos as repos
            on events.repo_artifact_id = repos.repo_artifact_id
        where events.event_type = 'COMMIT_CODE'
        group by
            repos.project_id,
            repos.sample_date,
            events.developer_id,
            events.developer_name
    ),

    eligible_developers as (
        select distinct developer_id
        from developer_activity
        where
            total_commits_to_project >= @commits_threshold
            and months_between(last_commit, first_commit) >= @active_months_threshold
            and date(last_commit)
            >= current_date() - interval @last_commit_threshold_months month
    )

select
    sample_date,
    project_id,
    developer_id,
    developer_name,
    total_commits_to_project,
    first_commit,
    last_commit
from developer_activity
where developer_id in (select developer_id from eligible_developers)
