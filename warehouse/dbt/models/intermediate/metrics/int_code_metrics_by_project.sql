{{
  config(
    materialized='table'
  )
}}

with metrics as (
  select * from {{ ref('int_code_metric__active_developers') }}
  union all
  select * from {{ ref('int_code_metric__commits_prs_issues') }}
  union all
  select * from {{ ref('int_code_metric__contributors') }}
  union all
  select *
  from {{ ref('int_code_metric__fulltime_developers_average') }}
  union all
  select * from {{ ref('int_code_metric__new_contributors') }}
  union all
  select * from {{ ref('int_code_metric__time_to_first_response_days_average') }}
  union all
  select * from {{ ref('int_code_metric__time_to_merge_days_average') }}
),

aggs as (
  select
    project_id,
    event_source,
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
          metric in ('pull_request_review_comment_count', 'issue_comment_count')
          and time_interval = '6 MONTHS'
          then amount
        else 0
      end
    ) as comment_count_6_months,
    SUM(
      case
        when
          metric = 'release_published_count'
          and time_interval = '6 MONTHS'
          then amount
        else 0
      end
    ) as release_count_6_months,
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
          metric = 'active_developer_count'
          and time_interval = 'ALL'
          then amount
        else 0
      end
    ) as developer_count,
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
          metric = 'fulltime_developer_average'
          and time_interval = '6 MONTHS'
          then amount
        else 0
      end
    ) as fulltime_developer_average_6_months,
    SUM(
      case
        when
          metric = 'time_to_first_response_days_average'
          and time_interval = '6 MONTHS'
          then amount
        else 0
      end
    ) as time_to_first_response_days_average_6_months,
    SUM(
      case
        when
          metric = 'time_to_merge_days_average'
          and time_interval = '6 MONTHS'
          then amount
        else 0
      end
    ) as time_to_merge_days_average_6_months
  from metrics
  group by
    project_id,
    event_source
),

repos as (
  select
    project_id,
    artifact_source as event_source,
    MIN(created_at) as first_created_at_date,
    MAX(updated_at) as last_updated_at_date,
    MIN(first_commit_time) as first_commit_date,
    MAX(last_commit_time) as last_commit_date,
    COUNT(distinct artifact_id) as repository_count,
    SUM(star_count) as star_count,
    SUM(fork_count) as fork_count
  from {{ ref('int_repo_metrics_by_project') }}
  group by
    project_id,
    artifact_source
),

code_metrics as (
  select
    repos.*,
    aggs.* except (project_id, event_source)
  from repos
  left join aggs
    on
      repos.project_id = aggs.project_id
      and repos.event_source = aggs.event_source
),

project_metadata as (
  select
    project_id,
    project_source,
    project_namespace,
    project_name,
    display_name,
    'GITHUB' as event_source
  from {{ ref('int_projects') }}

)

select
  project_metadata.project_id,
  project_metadata.project_source,
  project_metadata.project_namespace,
  project_metadata.project_name,
  project_metadata.display_name,
  project_metadata.event_source,
  code_metrics.first_created_at_date,
  code_metrics.last_updated_at_date,
  code_metrics.first_commit_date,
  code_metrics.last_commit_date,
  code_metrics.repository_count,
  code_metrics.star_count,
  code_metrics.fork_count,
  code_metrics.developer_count,
  code_metrics.contributor_count,
  code_metrics.contributor_count_6_months,
  code_metrics.new_contributor_count_6_months,
  code_metrics.fulltime_developer_average_6_months,
  code_metrics.active_developer_count_6_months,
  code_metrics.commit_count_6_months,
  code_metrics.opened_pull_request_count_6_months,
  code_metrics.merged_pull_request_count_6_months,
  code_metrics.opened_issue_count_6_months,
  code_metrics.closed_issue_count_6_months,
  code_metrics.comment_count_6_months,
  code_metrics.release_count_6_months,
  code_metrics.time_to_first_response_days_average_6_months,
  code_metrics.time_to_merge_days_average_6_months
from project_metadata
left join code_metrics
  on
    project_metadata.project_id = code_metrics.project_id
    and project_metadata.event_source = code_metrics.event_source
where code_metrics.event_source is not null
