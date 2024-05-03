with ranked_repos as (
  select
    project_id,
    owner,
    star_count,
    ROW_NUMBER() over (
      partition by project_id order by star_count desc
    ) as row_number,
    COUNT(distinct owner)
      over (partition by project_id)
      as count_github_owners
  from {{ ref('stg_ossd__repositories_by_project') }}
)

select
  project_id,
  count_github_owners,
  LOWER(owner) as primary_github_owner
--TODO: is_git_organization
from ranked_repos
where row_number = 1
