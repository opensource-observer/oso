model(
    name oso.stg_github__distinct_commits_resolved_mergebot,
    description 'Resolve merges that were created by the mergebot',
    kind full,
)
;

with
    merge_bot_commits as (
        select * from oso.stg_github__distinct_main_commits where actor_id = 118344674
    ),

    resolved_merge_bot_commits as (
        select
            mbc.repository_id,
            mbc.sha,
            mbc.created_at,
            mbc.repository_name,
            mbc.push_id,
            mbc.ref,
            ghprme.actor_id,
            ghprme.actor_login,
            mbc.author_email,
            mbc.author_name,
            mbc.is_distinct,
            mbc.api_url
        from merge_bot_commits as mbc
        inner join
            oso.stg_github__pull_request_merge_events as ghprme
            on mbc.repository_id = ghprme.repository_id
            and mbc.sha = ghprme.merge_commit_sha
    ),

    no_merge_bot_commits as (
        select *
        from oso.stg_github__distinct_main_commits
        {# The following is the actor_id for the github merge bot #}
        where actor_id != 118344674
    )

select *
from resolved_merge_bot_commits
union all
select *
from no_merge_bot_commits
