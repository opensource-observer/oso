{% set date_6_months = "DATE_TRUNC(CURRENT_DATE(), month) - INTERVAL 6 MONTH" %}

with repos as (
  select
    project_id,
    MIN(first_commit_time) as first_commit_date,
    MAX(last_commit_time) as last_commit_date,
    COUNT(distinct artifact_id) as repositories,
    SUM(star_count) as stars,
    SUM(fork_count) as forks
  from {{ ref('int_repo_metrics_by_project') }}
  --WHERE r.is_fork = false
  group by project_id
),

project_repos_summary as (
  select
    repos.project_id,
    repos.first_commit_date,
    repos.last_commit_date,
    repos.repositories,
    repos.stars,
    repos.forks,
    int_projects.project_source,
    int_projects.project_namespace,
    int_projects.project_name,
    int_projects.display_name
  from repos
  left join {{ ref('int_projects') }}
    on repos.project_id = int_projects.project_id
),

dev_activity as (
  select
    project_id,
    from_artifact_id,
    bucket_month,
    user_segment_type,
    case
      when DATE(bucket_month) >= {{ date_6_months }} then 1
      else 0
    end as is_last_6_months,
    case
      when
        DATE(bucket_month) >= {{ date_6_months }}
        and LAG(bucket_month) over (
          partition by project_id, from_artifact_id
          order by bucket_month
        ) is null
        then 1
      else 0
    end as is_new_last_6_months
  from {{ ref('int_developer_status_monthly_by_project') }}
),

contribs_cte as (
  select
    project_id,
    COUNT(distinct from_artifact_id) as contributors,
    COUNT(
      distinct
      case
        when is_last_6_months = 1 then from_artifact_id
      end
    ) as contributors_6_months,
    COUNT(
      distinct
      case
        when is_new_last_6_months = 1 then from_artifact_id
      end
    ) as new_contributors_6_months,
    AVG(
      case
        when
          is_last_6_months = 1
          and user_segment_type = 'FULL_TIME_DEVELOPER'
          then 1
        else 0
      end
    ) as avg_fulltime_devs_6_months,
    AVG(
      case
        when
          is_last_6_months = 1
          and user_segment_type in (
            'FULL_TIME_DEVELOPER',
            'PART_TIME_DEVELOPER'
          ) then 1
        else 0
      end
    ) as avg_active_devs_6_months
  from dev_activity
  group by project_id
),

activity_cte as (
  select
    project_id,
    SUM(
      case
        when event_type = 'COMMIT_CODE' then amount
      end
    ) as commits_6_months,
    SUM(
      case
        when event_type = 'ISSUE_OPENED' then amount
      end
    ) as issues_opened_6_months,
    SUM(
      case
        when event_type = 'ISSUE_CLOSED' then amount
      end
    ) as issues_closed_6_months,
    SUM(
      case
        when event_type = 'PULL_REQUEST_OPENED' then amount
      end
    ) as pull_requests_opened_6_months,
    SUM(
      case
        when event_type = 'PULL_REQUEST_MERGED' then amount
      end
    ) as pull_requests_merged_6_months
  from {{ ref('int_events_daily_to_project') }}
  where
    event_source = 'GITHUB'
    and event_type in (
      'COMMIT_CODE',
      'ISSUE_OPENED',
      'ISSUE_CLOSED',
      'PULL_REQUEST_OPENED',
      'PULL_REQUEST_MERGED'
    )
    and DATE_DIFF(CURRENT_DATE(), DATE(bucket_day), month) <= 6
  group by project_id
)

select
  p.project_id,
  p.project_source,
  p.project_namespace,
  p.project_name,
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
  on p.project_id = c.project_id
left join activity_cte as a
  on p.project_id = a.project_id
