{{
  config(
    materialized='table'
  )
}}

{% set min_repo_stars = 5 %}
{% set last_repo_update_date = '2024-07-01' %}
{% set active_months_threshold = 3 %}
{% set commits_threshold = 20 %}
{% set last_commit_threshold_months = 12 %}

with eligible_onchain_builder_repos as (
  select
    repo_artifact_id,
    project_id as onchain_builder_project_id
  from {{ ref('int_superchain_s7_repositories') }}
  where
    language in ('TypeScript', 'Solidity', 'Rust')
    and updated_at > '{{ last_repo_update_date }}'
    and star_count > {{ min_repo_stars }}
    and project_id in (
      select project_id
      from {{ ref('int_superchain_s7_onchain_builder_eligibility') }}
      where is_eligible
    )
),

eligible_devtooling_repos as (
  select
    repo_artifact_id,
    project_id as devtooling_project_id
  from {{ ref('int_superchain_s7_devtooling_eligibility') }}
  where is_eligible
),

developer_activity as (
  select
    users.user_id as developer_id,
    users.display_name as developer_name,
    events.to_artifact_id as repo_artifact_id,
    count(distinct date_trunc(events.time, month)) as active_months,
    sum(events.amount) as total_commits,
    max(date(events.time)) as last_commit
  from {{ ref('int_events__github') }} as events
  inner join {{ ref('int_users') }} as users
    on events.from_artifact_id = users.user_id
  inner join eligible_onchain_builder_repos
    on events.to_artifact_id = eligible_onchain_builder_repos.repo_artifact_id
  where
    events.event_type = 'COMMIT_CODE'
    and not regexp_contains(
      users.display_name,
      r'(^|[^a-zA-Z0-9_])bot([^a-zA-Z0-9_]|$)|bot$'
    )
  group by 1, 2, 3
  having
    total_commits >= {{ commits_threshold }}
    and active_months >= {{ active_months_threshold }}
    and last_commit >= date_sub(
      current_date(),
      interval {{ last_commit_threshold_months }} month
    )
),

developer_events as (
  select
    dev.developer_id,
    dev.developer_name,
    events.to_artifact_id as repo_artifact_id,
    sum(case when events.event_type = 'COMMIT_CODE' then amount else 0 end)
      as total_commits_to_repo,
    max(coalesce(events.event_type = 'STARRED', false)) as has_starred,
    max(coalesce(events.event_type = 'FORKED', false)) as has_forked,
    max(coalesce(events.event_type in (
      'PULL_REQUEST_CREATED',
      'PULL_REQUEST_MERGED',
      'COMMIT_CODE'
    ), false)) as has_code_contribution,
    max(coalesce(events.event_type in (
      'ISSUE_OPENED',
      'ISSUE_COMMENTED'
    ), false)) as has_issue_contribution,
    sum(case
      when events.event_type != 'STARRED'
        then coalesce(events.amount, 1)
      else 0
    end) as total_non_star_events,
    min(date(events.time)) as first_event,
    max(date(events.time)) as last_event
  from {{ ref('int_events__github') }} as events
  inner join developer_activity as dev
    on events.from_artifact_id = dev.developer_id
  where
    events.event_type in (
      'STARRED',
      'FORKED',
      'PULL_REQUEST_CREATED',
      'PULL_REQUEST_MERGED',
      'COMMIT_CODE',
      'ISSUE_OPENED',
      'ISSUE_COMMENTED'
    )
  group by 1, 2, 3
),

developer_graph as (
  select
    de.developer_id,
    de.developer_name,
    de.repo_artifact_id,
    de.has_starred,
    de.has_forked,
    de.has_code_contribution,
    de.has_issue_contribution,
    de.total_commits_to_repo,
    de.total_non_star_events as total_non_star_events_to_repo,
    de.first_event as first_event_to_repo,
    de.last_event as last_event_to_repo,
    current_timestamp() as sample_date,
    coalesce(dtr.devtooling_project_id, obr.onchain_builder_project_id)
      as project_id,
    coalesce(dtr.devtooling_project_id is not null, false)
      as is_devtooling_project,
    coalesce(obr.onchain_builder_project_id is not null, false)
      as is_onchain_builder_project,
    coalesce(da.developer_id is not null, false)
      as is_developers_onchain_builder_project
  from developer_events as de
  left join eligible_devtooling_repos as dtr
    on de.repo_artifact_id = dtr.repo_artifact_id
  left join eligible_onchain_builder_repos as obr
    on de.repo_artifact_id = obr.repo_artifact_id
  left join developer_activity as da
    on
      de.developer_id = da.developer_id
      and de.repo_artifact_id = da.repo_artifact_id
)

select * from developer_graph
where project_id is not null
