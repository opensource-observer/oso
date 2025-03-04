model(name oso.stg_github__issues, kind full,)
;

with
    issue_events as (
        select *
        from @oso_source('bigquery.oso.stg_github__events') as ghe
        where ghe.type = 'IssuesEvent'
    )

select
    ie.id as id,
    ie.created_at as event_time,
    ie.repo.id as repository_id,
    ie.repo.name as repository_name,
    ie.actor.id as actor_id,
    ie.actor.login as actor_login,
    concat('ISSUE_', upper(json_extract_string(ie.payload, '$.action'))) as "type",
    json_extract(ie.payload, '$.issue.number')::bigint as "number",
    strptime(
        json_extract_string(ie.payload, '$.issue.created_at'), '%Y-%m-%dT%H:%M:%SZ'
    ) as created_at,
    strptime(
        json_extract_string(ie.payload, '$.issue.closed_at'), '%Y-%m-%dT%H:%M:%SZ'
    ) as closed_at,
    json_extract_string(ie.payload, '$.issue.state') as "state",
    json_extract(ie.payload, '$.issue.comments')::double as comments
from issue_events as ie
