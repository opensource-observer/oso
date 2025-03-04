model(name oso.stg_github__comments, kind full,)
;

with
    pull_request_comment_events as (
        select
            ghe.id as id,
            ghe.created_at as event_time,
            ghe.repo.id as repository_id,
            ghe.repo.name as repository_name,
            ghe.actor.id as actor_id,
            ghe.actor.login as actor_login,
            'PULL_REQUEST_REVIEW_COMMENT' as "type",
            json_extract(ghe.payload, '$.pull_request.number')::bigint as "number",
            strptime(
                json_extract_string(ghe.payload, '$.pull_request.created_at'),
                '%Y-%m-%dT%H:%M:%SZ'
            ) as created_at,
            strptime(
                json_extract_string(ghe.payload, '$.pull_request.merged_at'),
                '%Y-%m-%dT%H:%M:%SZ'
            ) as merged_at,
            strptime(
                json_extract_string(ghe.payload, '$.pull_request.closed_at'),
                '%Y-%m-%dT%H:%M:%SZ'
            ) as closed_at,
            json_extract_string(ghe.payload, '$.pull_request.state') as "state",
            json_extract(ghe.payload, '$.pull_request.comments')::double as comments
        from @oso_source('bigquery.oso.stg_github__events') as ghe
        where ghe.type = 'PullRequestReviewCommentEvent'
    ),

    issue_comment_events as (
        select
            ghe.id as id,
            ghe.created_at as "event_time",
            ghe.repo.id as repository_id,
            ghe.repo.name as repository_name,
            ghe.actor.id as actor_id,
            ghe.actor.login as actor_login,
            'ISSUE_COMMENT' as "type",
            json_extract(ghe.payload, '$.issue.number')::int as "number",
            strptime(
                json_extract_string(ghe.payload, '$.issue.created_at'),
                '%Y-%m-%dT%H:%M:%SZ'
            ) as created_at,
            cast(null as timestamp) as merged_at,
            strptime(
                json_extract_string(ghe.payload, '$.issue.closed_at'),
                '%Y-%m-%dT%H:%M:%SZ'
            ) as closed_at,
            json_extract_string(ghe.payload, '$.issue.state') as "state",
            json_extract(ghe.payload, '$.issue.comments')::double as comments
        from @oso_source('bigquery.oso.stg_github__events') as ghe
        where ghe.type = 'IssueCommentEvent'
    )

select *
from pull_request_comment_events
union all
select *
from issue_comment_events
