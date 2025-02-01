{{
  config(
    materialized='table'
  )
}}

{% set lookback_days = 180 %}


select
  project_id,
  repo_artifact_id,
  last_release_published,
  has_npm_package,
  has_rust_package,
  num_dependent_repos_in_oso,
  is_fork,
  created_at,
  updated_at,
  case when (
    date(last_release_published)
    >= date_sub(current_date(), interval {{ lookback_days }} day)
    or has_npm_package
    or has_rust_package
    or num_dependent_repos_in_oso > 0
  ) then true else false end as is_eligible
from {{ ref('int_superchain_s7_repositories') }}
