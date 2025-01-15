{% set active_months_threshold = 3 %}
{% set commits_threshold = 20 %}
{% set last_commit_threshold_months = 12 %}

with developers as (
  select
    users.user_id as developer_id,
    users.display_name as developer_name,
    coalesce(max(repositories.language = 'Solidity'), false)
      as is_solidity_developer,
    sum(events.amount) as total_commits,
    count(distinct date_trunc(events.time, month)) as active_months,
    min(date(events.time)) as first_commit,
    max(date(events.time)) as last_commit,
    array_agg(distinct repositories.project_id) as onchain_projects
  from {{ ref('int_events__github') }} as events
  inner join {{ ref('users_v1') }} as users
    on events.from_artifact_id = users.user_id
  inner join {{ ref('repositories_v0') }} as repositories
    on events.to_artifact_id = repositories.artifact_id
  where
    events.event_type = 'COMMIT_CODE'
    and not regexp_contains(
      users.display_name, r'(^|[^a-zA-Z0-9_])bot([^a-zA-Z0-9_]|$)|bot$'
    )
    and repositories.language in ('TypeScript', 'Solidity', 'Rust')
    and repositories.project_id in (
      select distinct project_id
      from {{ ref('int_superchain_onchain_builder_filter') }}
    )
  group by
    users.user_id,
    users.display_name
)

select * from developers
where
  total_commits >= {{ commits_threshold }}
  and active_months >= {{ active_months_threshold }}
  and last_commit >= date_sub(current_date(), interval {{ last_commit_threshold_months }} month)
order by developer_name
