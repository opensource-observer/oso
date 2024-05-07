{# 
  New contributors to a project in a given time interval  
#}

with contributors as (
  select
    project_id,
    artifact_id,
    MIN(first_contribution_time) as first_contribution_time
  from {{ ref('int_contributors_to_project') }}
  group by
    project_id,
    artifact_id
)

select
  contributors.project_id,
  int_time_intervals.time_interval,
  'NEW_CONTRIBUTORS_TOTAL' as impact_metric,
  COUNT(distinct case
    when
      DATE(contributors.first_contribution_time)
      >= DATE_TRUNC(int_time_intervals.start_date, month)
      then contributors.artifact_id
  end) as amount
from contributors
cross join {{ ref('int_time_intervals') }}
group by
  contributors.project_id,
  int_time_intervals.time_interval
