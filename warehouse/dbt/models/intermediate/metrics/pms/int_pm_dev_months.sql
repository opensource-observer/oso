{# 
  This model calculates the total man-months of developer activity
  for each project in various time ranges.

  The model uses the int_active_devs_monthly_to_project model to segment
  developers based on monthly activity using the Electric Capital
  Developer Report taxonomy.
#}

select
  e.project_id,
  t.time_interval,
  CONCAT(e.user_segment_type, '_TOTAL') as impact_metric,
  COUNT(distinct e.from_artifact_id) as amount
from {{ ref('int_developer_status_monthly_by_project') }} as e
cross join {{ ref('int_time_intervals') }} as t
where
  DATE(e.bucket_month) >= DATE_TRUNC(t.start_date, month)
  and DATE(e.bucket_month) < DATE_TRUNC(CURRENT_DATE(), month)
group by
  e.project_id,
  t.time_interval,
  e.user_segment_type
