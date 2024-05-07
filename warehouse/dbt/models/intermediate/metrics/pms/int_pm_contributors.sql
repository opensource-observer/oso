{# 
  Contributors to a project in a time interval
#}

select
  int_contributors_to_project.project_id,
  int_time_intervals.time_interval,
  CONCAT('CONTRIBUTORS_TOTAL') as impact_metric,
  COUNT(distinct int_contributors_to_project.artifact_id) as amount
from {{ ref('int_contributors_to_project') }}
cross join {{ ref('int_time_intervals') }}
group by
  int_contributors_to_project.project_id,
  int_time_intervals.time_interval
