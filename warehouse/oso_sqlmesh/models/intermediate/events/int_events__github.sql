model(
    name oso.int_events__github,
    kind incremental_by_time_range(
        time_column time, batch_size 365, batch_concurrency 1
    ),
    start '2015-01-01',
    cron '@daily',
    partitioned_by(day("time"), "event_type"),
    grain(time, event_type, event_source, from_artifact_id, to_artifact_id)
)
;

with
    github_commits as (
        select  -- noqa: ST06
            created_at as "time",
            'COMMIT_CODE' as event_type,
            cast(push_id as string) as event_source_id,
            'GITHUB' as event_source,
            split(replace(repository_name, '@', ''), '/')[@array_index(1)] as to_name,
            split(replace(repository_name, '@', ''), '/')[
                @array_index(0)
            ] as to_namespace,
            'REPOSITORY' as to_type,
            cast(repository_id as string) as to_artifact_source_id,
            coalesce(actor_login, author_email) as from_name,
            coalesce(actor_login, author_email) as from_namespace,
            case
                when actor_login is not null then 'GIT_USER' else 'GIT_EMAIL'
            end as from_type,
            case
                when actor_login is not null
                then cast(actor_id as string)
                else author_email
            end as from_artifact_source_id,
            cast(1 as double) as amount
        from oso.stg_github__distinct_commits_resolved_mergebot
        where created_at between @start_dt and @end_dt
    ),

    github_releases as (
        select  -- noqa: ST06
            created_at as "time",
            type as event_type,
            cast(id as string) as event_source_id,
            'GITHUB' as event_source,
            split(replace(repository_name, '@', ''), '/')[@array_index(1)] as to_name,
            split(replace(repository_name, '@', ''), '/')[
                @array_index(0)
            ] as to_namespace,
            'REPOSITORY' as to_type,
            cast(repository_id as string) as to_artifact_source_id,
            actor_login as from_name,
            actor_login as from_namespace,
            'GIT_USER' as from_type,
            cast(actor_id as string) as from_artifact_source_id,
            cast(1 as double) as amount
        from oso.stg_github__releases
        where created_at between @start_dt and @end_dt
    ),

    github_comments as (
        select  -- noqa: ST06
            event_time as "time",
            type as event_type,
            cast(id as string) as event_source_id,
            'GITHUB' as event_source,
            split(replace(repository_name, '@', ''), '/')[@array_index(1)] as to_name,
            split(replace(repository_name, '@', ''), '/')[
                @array_index(0)
            ] as to_namespace,
            'REPOSITORY' as to_type,
            cast(repository_id as string) as to_artifact_source_id,
            actor_login as from_name,
            actor_login as from_namespace,
            'GIT_USER' as from_type,
            cast(actor_id as string) as from_artifact_source_id,
            cast(1 as double) as amount
        from oso.stg_github__comments
        where event_time between @start_dt and @end_dt
    ),

    github_issues as (
        select  -- noqa: ST06
            event_time as "time",
            type as event_type,
            cast(id as string) as event_source_id,
            'GITHUB' as event_source,
            split(replace(repository_name, '@', ''), '/')[@array_index(1)] as to_name,
            split(replace(repository_name, '@', ''), '/')[
                @array_index(0)
            ] as to_namespace,
            'REPOSITORY' as to_type,
            cast(repository_id as string) as to_artifact_source_id,
            actor_login as from_name,
            actor_login as from_namespace,
            'GIT_USER' as from_type,
            cast(actor_id as string) as from_artifact_source_id,
            cast(1 as double) as amount
        from oso.stg_github__issues
        where event_time between @start_dt and @end_dt
    ),

    github_pull_requests as (
        select  -- noqa: ST06
            event_time as "time",
            type as event_type,
            cast(id as string) as event_source_id,
            'GITHUB' as event_source,
            split(replace(repository_name, '@', ''), '/')[@array_index(1)] as to_name,
            split(replace(repository_name, '@', ''), '/')[
                @array_index(0)
            ] as to_namespace,
            'REPOSITORY' as to_type,
            cast(repository_id as string) as to_artifact_source_id,
            actor_login as from_name,
            actor_login as from_namespace,
            'GIT_USER' as from_type,
            cast(actor_id as string) as from_artifact_source_id,
            cast(1 as double) as amount
        from oso.stg_github__pull_requests
        where event_time between @start_dt and @end_dt
    ),

    github_pull_request_merge_events as (
        select  -- noqa: ST06
            event_time as "time",
            type as event_type,
            cast(id as string) as event_source_id,
            'GITHUB' as event_source,
            split(replace(repository_name, '@', ''), '/')[@array_index(1)] as to_name,
            split(replace(repository_name, '@', ''), '/')[
                @array_index(0)
            ] as to_namespace,
            'REPOSITORY' as to_type,
            cast(repository_id as string) as to_artifact_source_id,
            actor_login as from_name,
            actor_login as from_namespace,
            'GIT_USER' as from_type,
            cast(actor_id as string) as from_artifact_source_id,
            cast(1 as double) as amount
        from oso.stg_github__pull_request_merge_events
        where event_time between @start_dt and @end_dt
    ),

    github_stars_and_forks as (
        select  -- noqa: ST06
            created_at as "time",
            type as event_type,
            cast(id as string) as event_source_id,
            'GITHUB' as event_source,
            split(replace(repository_name, '@', ''), '/')[@array_index(1)] as to_name,
            split(replace(repository_name, '@', ''), '/')[
                @array_index(0)
            ] as to_namespace,
            'REPOSITORY' as to_type,
            cast(repository_id as string) as to_artifact_source_id,
            actor_login as from_name,
            actor_login as from_namespace,
            'GIT_USER' as from_type,
            cast(actor_id as string) as from_artifact_source_id,
            cast(1 as double) as amount
        from oso.stg_github__stars_and_forks
        where created_at between @start_dt and @end_dt
    ),

    all_events as (
        select
            time,
            event_type,
            event_source_id,
            event_source,
            @oso_id(event_source, to_artifact_source_id) as to_artifact_id,
            to_name as to_artifact_name,
            to_namespace as to_artifact_namespace,
            to_type as to_artifact_type,
            to_artifact_source_id,
            @oso_id(event_source, from_artifact_source_id) as from_artifact_id,
            from_name as from_artifact_name,
            from_namespace as from_artifact_namespace,
            from_type as from_artifact_type,
            from_artifact_source_id,
            amount
        from
            (
                select *
                from github_commits
                union all
                select *
                from github_issues
                union all
                select *
                from github_pull_requests
                union all
                select *
                from github_pull_request_merge_events
                union all
                select *
                from github_releases
                union all
                select *
                from github_stars_and_forks
                union all
                select *
                from github_comments
            )
    )

select
    time,
    to_artifact_id,
    from_artifact_id,
    upper(event_type) as event_type,
    cast(event_source_id as string) as event_source_id,
    upper(event_source) as event_source,
    lower(to_artifact_name) as to_artifact_name,
    lower(to_artifact_namespace) as to_artifact_namespace,
    upper(to_artifact_type) as to_artifact_type,
    lower(to_artifact_source_id) as to_artifact_source_id,
    lower(from_artifact_name) as from_artifact_name,
    lower(from_artifact_namespace) as from_artifact_namespace,
    upper(from_artifact_type) as from_artifact_type,
    lower(from_artifact_source_id) as from_artifact_source_id,
    cast(amount as double) as amount
from all_events
