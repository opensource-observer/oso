with metrics as (
  select * from {{ ref('int_code_metric__active_developers') }}
  union all
  select * from {{ ref('int_code_metric__commits_prs_issues') }}
  union all
  select * from {{ ref('int_code_metric__contributors') }}
  union all
  select * from {{ ref('int_code_metric__fulltime_developers_avg') }}
  union all
  select * from {{ ref('int_code_metric__new_contributors') }}
),

aggs as (
  select
    project_id,
    SUM(
      case
        when
          metric = 'commit_code_count'
          and time_interval = '6 MONTHS'
          then amount
        else 0
      end
    ) as commit_count_6_months,
    SUM(
      case
        when
          metric = 'pull_request_opened_count'
          and time_interval = '6 MONTHS'
          then amount
        else 0
      end
    ) as opened_pull_request_count_6_months,
    SUM(
      case
        when
          metric = 'pull_request_merged_count'
          and time_interval = '6 MONTHS'
          then amount
        else 0
      end
    ) as merged_pull_request_count_6_months,
    SUM(
      case
        when
          metric = 'issue_opened_count'
          and time_interval = '6 MONTHS'
          then amount
        else 0
      end
    ) as opened_issue_count_6_months,
    SUM(
      case
        when
          metric = 'issue_closed_count'
          and time_interval = '6 MONTHS'
          then amount
        else 0
      end
    ) as closed_issue_count_6_months,
    SUM(
      case
        when
          metric = 'active_developer_count'
          and time_interval = '6 MONTHS'
          then amount
        else 0
      end
    ) as active_developer_count_6_months,
    SUM(
      case
        when
          metric = 'contributor_count'
          and time_interval = 'ALL'
          then amount
        else 0
      end
    ) as contributor_count,
    SUM(
      case
        when
          metric = 'contributor_count'
          and time_interval = '6 MONTHS'
          then amount
        else 0
      end
    ) as contributor_count_6_months,
    SUM(
      case
        when
          metric = 'new_contributor_count'
          and time_interval = '6 MONTHS'
          then amount
        else 0
      end
    ) as new_contributor_count_6_months,
    SUM(
      case
        when
          metric = 'fulltime_developer_avg'
          and time_interval = '6 MONTHS'
          then amount
        else 0
      end
    ) as fulltime_developer_avg_6_months
  from metrics
  group by project_id
),

repos as (
  select
    project_id,
    MIN(first_commit_time) as first_commit_date,
    MAX(last_commit_time) as last_commit_date,
    COUNT(distinct artifact_id) as repository_count,
    SUM(star_count) as star_count,
    SUM(fork_count) as fork_count
  from {{ ref('int_repo_metrics_by_project') }}
  --WHERE r.is_fork = false
  group by project_id
)

select
  int_projects.project_id,
  int_projects.project_source,
  int_projects.project_namespace,
  int_projects.project_name,
  int_projects.display_name,
  repos.first_commit_date,
  repos.last_commit_date,
  repos.repository_count,
  repos.star_count,
  repos.fork_count,
  aggs.contributor_count,
  aggs.contributor_count_6_months,
  aggs.new_contributor_count_6_months,
  aggs.fulltime_developer_avg_6_months,
  aggs.active_developer_count_6_months,
  aggs.commit_count_6_months,
  aggs.opened_pull_request_count_6_months,
  aggs.merged_pull_request_count_6_months,
  aggs.opened_issue_count_6_months,
  aggs.closed_issue_count_6_months
from {{ ref('int_projects') }}
left join aggs
  on int_projects.project_id = aggs.project_id
left join repos
  on int_projects.project_id = repos.project_id
