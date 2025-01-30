{{
  config(
    materialized='table'
  )
}}

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
)

select *
from eligible_repos
