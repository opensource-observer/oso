{{
  config(
    materialized='table'
  )
}}

{% set min_repo_stars = 5 %}
{% set last_repo_update_date = '2024-07-01' %}


with repo_stats as (
  select
    project_id as devtooling_project_id,
    artifact_id as repo_artifact_id,
    artifact_namespace as repo_owner,
    artifact_name as repo_name,
    language as repo_language,
    created_at as repo_created_at,
    updated_at as repo_updated_at,
    star_count as repo_stars,
    fork_count as repo_forks
  from {{ ref('int_repositories') }}
),

releases as (
  select
    repo_stats.repo_artifact_id,
    max(events.time) as last_release_published
  from repo_stats
  inner join {{ ref('int_events__github') }} as events
    on repo_stats.repo_artifact_id = events.to_artifact_id
  where events.event_type = 'RELEASE_PUBLISHED'
  group by repo_artifact_id
),

all_eligible_repos as (
  select
    repo_stats.*,
    releases.last_release_published
  from repo_stats
  inner join releases
    on repo_stats.repo_artifact_id = releases.repo_artifact_id
  where
    repo_stats.repo_updated_at > '{{ last_repo_update_date }}'
    and repo_stats.repo_stars > {{ min_repo_stars }}
    and releases.last_release_published > '{{ last_repo_update_date }}'
),

events_by_trusted_developer as (
  select
    devs.developer_id,
    devs.developer_name,
    events.to_artifact_id as repo_artifact_id,
    events.event_type,
    sum(events.amount) as total_events,
    min(date(events.time)) as first_event,
    max(date(events.time)) as last_event
  from {{ ref('int_events__github') }} as events
  inner join {{ ref('int_superchain_s7_trusted_developers') }} as devs
    on events.from_artifact_id = devs.developer_id
  inner join all_eligible_repos
    on events.to_artifact_id = all_eligible_repos.repo_artifact_id
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
    and events.to_artifact_namespace != devs.repo_owner
  group by
    devs.developer_id,
    devs.developer_name,
    events.to_artifact_id,
    events.event_type
),

dev_event_summaries as (
  select
    developer_id,
    developer_name,
    repo_artifact_id,
    max(coalesce(event_type = 'STARRED', false))
      as has_starred,
    max(coalesce(event_type = 'FORKED', false))
      as has_forked,
    max(coalesce(event_type in (
      'PULL_REQUEST_CREATED',
      'PULL_REQUEST_MERGED',
      'COMMIT_CODE'
    ), false)) as has_code_contribution,
    max(coalesce(event_type in (
      'ISSUE_OPENED',
      'ISSUE_COMMENTED'
    ), false)) as has_issue_contribution,
    sum(
      case when event_type != 'STARRED' then total_events else 0 end
    ) as total_non_star_events_to_repo,
    min(first_event) as first_event_to_repo,
    max(last_event) as last_event_to_repo
  from events_by_trusted_developer
  group by
    repo_artifact_id,
    developer_id,
    developer_name
)

select
  dev_event_summaries.developer_id,
  dev_event_summaries.developer_name,
  repos.devtooling_project_id,
  repos.repo_artifact_id,
  repos.repo_owner,
  repos.repo_name,
  repos.repo_stars,
  repos.repo_forks,
  repos.repo_language,
  repos.repo_created_at,
  repos.repo_updated_at,
  repos.last_release_published,
  dev_event_summaries.has_starred,
  dev_event_summaries.has_forked,
  dev_event_summaries.has_code_contribution,
  dev_event_summaries.has_issue_contribution,
  dev_event_summaries.total_non_star_events_to_repo,
  dev_event_summaries.first_event_to_repo,
  dev_event_summaries.last_event_to_repo
from dev_event_summaries
inner join all_eligible_repos as repos
  on dev_event_summaries.repo_artifact_id = repos.repo_artifact_id
