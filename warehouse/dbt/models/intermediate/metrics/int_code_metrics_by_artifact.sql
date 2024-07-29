{{
  config(
    materialized='table'
  )
}}

with metrics as (
  select * from {{ ref('int_code_metric_artifact__active_developers') }}
  union all
  select * from {{ ref('int_code_metric_artifact__commits_prs_issues') }}
  union all
  select * from {{ ref('int_code_metric_artifact__contributors') }}
  union all
  select *
  from {{ ref('int_code_metric_artifact__fulltime_developers_average') }}
  union all
  select * from {{ ref('int_code_metric_artifact__new_contributors') }}
),

aggs as (
  select
    to_artifact_id as artifact_id,
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
          metric = 'fulltime_developer_average'
          and time_interval = '6 MONTHS'
          then amount
        else 0
      end
    ) as fulltime_developer_average_6_months
  from metrics
  group by
    to_artifact_id,
    event_source
),

repos as (
  select
    artifact_id,
    artifact_namespace,
    artifact_name,
    artifact_source as event_source,
    MIN(first_commit_time) as first_commit_date,
    MAX(last_commit_time) as last_commit_date,
    MAX(distinct artifact_id) as repository_count,
    MAX(star_count) as star_count,
    MAX(fork_count) as fork_count
  from {{ ref('int_repo_metrics_by_project') }}
  group by
    artifact_id,
    artifact_namespace,
    artifact_name,
    artifact_source
),

code_metrics as (
  select
    repos.*,
    aggs.* except (artifact_id, event_source)
  from repos
  left join aggs
    on
      repos.artifact_id = aggs.artifact_id
      and repos.event_source = aggs.event_source
)

select
  artifact_id,
  artifact_namespace,
  artifact_name,
  event_source,
  first_commit_date,
  last_commit_date,
  repository_count,
  star_count,
  fork_count,
  contributor_count,
  contributor_count_6_months,
  new_contributor_count_6_months,
  fulltime_developer_average_6_months,
  active_developer_count_6_months,
  commit_count_6_months,
  opened_pull_request_count_6_months,
  merged_pull_request_count_6_months,
  opened_issue_count_6_months,
  closed_issue_count_6_months
from code_metrics
where event_source is not null
