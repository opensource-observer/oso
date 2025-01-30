{{
  config(
    materialized='table'
  )
}}

{% set active_months_threshold = 3 %}
{% set commits_threshold = 20 %}
{% set last_commit_threshold_months = 12 %}
{% set min_repo_stars = 5 %}
{% set last_repo_update_date = '2024-07-01' %}


with eligible_repos as (
  select
    projects.sample_date,
    projects.project_id,
    repositories.artifact_id as repo_artifact_id,
    repositories.artifact_namespace as repo_owner,
    repositories.artifact_name as repo_name,
    repositories.language as repo_language,
    repositories.created_at as repo_created_at,
    repositories.updated_at as repo_updated_at,
    repositories.star_count as repo_stars,
    repositories.fork_count as repo_forks,
    projects.transaction_count as project_transaction_count,
    projects.gas_fees as project_gas_fees,
    projects.user_count as project_user_count
  from {{ ref('int_superchain_s7_onchain_builder_eligibility') }} as projects
  inner join {{ ref('int_repositories') }} as repositories
    on projects.project_id = repositories.project_id
  where
    projects.is_eligible
    and repositories.language in ('TypeScript', 'Solidity', 'Rust')
    and repositories.updated_at > '{{ last_repo_update_date }}'
    and repositories.star_count > {{ min_repo_stars }}
),

developers as (
  select
    eligible_repos.repo_artifact_id,
    users.user_id as developer_id,
    users.display_name as developer_name,
    sum(events.amount) as total_commits,
    count(distinct date_trunc(events.time, month)) as active_months,
    min(date(events.time)) as first_commit,
    max(date(events.time)) as last_commit
  from {{ ref('int_events__github') }} as events
  inner join {{ ref('int_users') }} as users
    on events.from_artifact_id = users.user_id
  inner join eligible_repos
    on events.to_artifact_id = eligible_repos.repo_artifact_id
  where
    events.event_type = 'COMMIT_CODE'
    and not regexp_contains(
      users.display_name, r'(^|[^a-zA-Z0-9_])bot([^a-zA-Z0-9_]|$)|bot$'
    )
  group by
    eligible_repos.repo_artifact_id,
    users.user_id,
    users.display_name
),

eligible_developers_by_repo as (
  select
    eligible_repos.*,
    developers.developer_id,
    developers.developer_name,
    developers.total_commits,
    developers.active_months,
    developers.first_commit,
    developers.last_commit
  from eligible_repos
  inner join developers
    on eligible_repos.repo_artifact_id = developers.repo_artifact_id
  where
    developers.total_commits >= {{ commits_threshold }}
    and developers.active_months >= {{ active_months_threshold }}
    and developers.last_commit
    >= date_sub(current_date(), interval {{ last_commit_threshold_months }} month)
)

select
  sample_date,
  developer_id,
  developer_name,
  total_commits as total_commits_to_repo,
  active_months as active_months_to_repo,
  first_commit as first_commit_to_repo,
  last_commit as last_commit_to_repo,
  repo_artifact_id,
  repo_owner,
  repo_name,
  repo_language,
  repo_created_at,
  repo_updated_at,
  repo_stars,
  repo_forks,
  project_id,
  project_transaction_count,
  project_gas_fees,
  project_user_count
from eligible_developers_by_repo
order by
  developer_name,
  repo_owner,
  repo_name
