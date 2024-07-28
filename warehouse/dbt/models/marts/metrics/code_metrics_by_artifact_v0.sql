{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  artifact_id,
  artifact_namespace,
  artifact_name,
  event_source,
  first_commit_date,
  last_commit_date,
  --repository_count,
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
from {{ ref('int_code_metrics_by_artifact') }}
