{# 
  Summary GitHub metrics for a project:
    - first_commit_date: The date of the first commit to the project
    - last_commit_date: The date of the last commit to the project
    - repos: The number of repositories in the project
    - stars: The number of stars the project has
    - forks: The number of forks the project has
    - contributors: The number of contributors to the project
    - contributors_6_months: The number of contributors to the project in the last 6 months
    - new_contributors_6_months: The number of new contributors to the project in the last 6 months    
    - avg_fulltime_devs_6_months: The number of full-time developers in the last 6 months
    - avg_active_devs_6_months: The average number of active developers in the last 6 months
    - commits_6_months: The number of commits to the project in the last 6 months
    - issues_opened_6_months: The number of issues opened in the project in the last 6 months
    - issues_closed_6_months: The number of issues closed in the project in the last 6 months
    - pull_requests_opened_6_months: The number of pull requests opened in the project in the last 6 months
    - pull_requests_merged_6_months: The number of pull requests merged in the project in the last 6 months
#}

with project_repos_summary as (
  select
    project_id,
    project_source,
    project_namespace,
    project_name,
    artifact_source,
    MIN(first_commit_time) as first_commit_date,
    MAX(last_commit_time) as last_commit_date,
    COUNT(distinct artifact_id) as repositories,
    SUM(star_count) as stars,
    SUM(fork_count) as forks
  from {{ ref('int_repos_by_project') }}
  --WHERE r.is_fork = false
  group by
    project_id,
    project_source,
    project_namespace,
    project_name,
    artifact_source
),

n_cte as (
  select
    project_id,
    artifact_source,
    SUM(case when time_interval = 'ALL' then amount end) as contributors,
    SUM(case when time_interval = '6M' then amount end)
      as new_contributors_6_months
  from {{ ref('int_pm_new_contribs') }}
  group by
    project_id,
    artifact_source
),

c_cte as (
  select
    project_id,
    artifact_source,
    SUM(amount) as contributors_6_months
  from {{ ref('int_pm_contributors') }}
  where time_interval = '6M'
  group by
    project_id,
    artifact_source
),

d_cte as (
  select
    project_id,
    artifact_source,
    SUM(
      case
        when impact_metric = 'FULL_TIME_DEV_TOTAL' then amount / 6
        else 0
      end
    ) as avg_fts_6_months,
    SUM(
      case
        when impact_metric = 'PART_TIME_DEV_TOTAL' then amount / 6
        else 0
      end
    ) as avg_pts_6_months
  from {{ ref('int_pm_dev_months') }}
  where time_interval = '6M'
  group by
    project_id,
    artifact_source
),

contribs_cte as (
  select
    n.project_id,
    n.artifact_source,
    n.contributors,
    n.new_contributors_6_months,
    c.contributors_6_months,
    d.avg_fts_6_months as avg_fulltime_devs_6_months,
    d.avg_fts_6_months + d.avg_pts_6_months as avg_active_devs_6_months
  from n_cte as n
  left join c_cte as c
    on
      n.project_id = c.project_id
      and n.artifact_source = c.artifact_source
  left join d_cte as d
    on
      n.project_id = d.project_id
      and n.artifact_source = d.artifact_source
),

activity_cte as (
  select
    project_id,
    artifact_source,
    SUM(
      case
        when impact_metric = 'COMMIT_CODE_TOTAL' then amount
      end
    ) as commits_6_months,
    SUM(
      case
        when impact_metric = 'ISSUE_OPENED_TOTAL' then amount
      end
    ) as issues_opened_6_months,
    SUM(
      case
        when impact_metric = 'ISSUE_CLOSED_TOTAL' then amount
      end
    ) as issues_closed_6_months,
    SUM(
      case
        when impact_metric = 'PULL_REQUEST_OPENED_TOTAL' then amount
      end
    ) as pull_requests_opened_6_months,
    SUM(
      case
        when impact_metric = 'PULL_REQUEST_MERGED_TOTAL' then amount
      end
    ) as pull_requests_merged_6_months
  from {{ ref('int_event_totals_by_project') }}
  where
    time_interval = '6M'
    and impact_metric in (
      'COMMIT_CODE_TOTAL',
      'ISSUE_OPENED_TOTAL',
      'ISSUE_CLOSED_TOTAL',
      'PULL_REQUEST_OPENED_TOTAL',
      'PULL_REQUEST_MERGED_TOTAL'
    )
  group by
    project_id,
    artifact_source
)


select
  p.project_id,
  p.project_source,
  p.project_namespace,
  p.project_name,
  p.artifact_source,
  p.first_commit_date,
  p.last_commit_date,
  p.repositories,
  p.stars,
  p.forks,
  c.contributors,
  c.contributors_6_months,
  c.new_contributors_6_months,
  c.avg_fulltime_devs_6_months,
  c.avg_active_devs_6_months,
  a.commits_6_months,
  a.issues_opened_6_months,
  a.issues_closed_6_months,
  a.pull_requests_opened_6_months,
  a.pull_requests_merged_6_months
from project_repos_summary as p
left join contribs_cte as c
  on
    p.project_id = c.project_id
    and p.artifact_source = c.artifact_source
left join activity_cte as a
  on
    p.project_id = a.project_id
    and p.artifact_source = a.artifact_source
