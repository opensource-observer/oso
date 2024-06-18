with repo_stats as (
  select
    project_id,
    count(distinct url) as total_repos,
    sum(case
      when license_check = 'Permissive' and repo_activity_check = 'OK' then 1
      else 0
    end) as eligible_repos
  from {{ ref('rf4_repo_stats_by_project') }}
  group by project_id
)

select
  project_id,
  'check_oss_requirements' as metric,
  cast((eligible_repos = total_repos) as int64) as amount
from repo_stats
where total_repos > 0
