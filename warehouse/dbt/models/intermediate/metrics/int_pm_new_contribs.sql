{# 
  
#}

select
  d.project_id,
  d.repository_source as artifact_source,
  t.time_interval,
  CONCAT('NEW_CONTRIBUTORS_TOTAL') as impact_metric,
  COUNT(distinct case
    when DATE(d.date_first_contribution) >= DATE_TRUNC(t.start_date, month)
      then d.from_id
  end) as amount
from {{ ref('int_devs') }} as d
cross join {{ ref('int_time_intervals') }} as t
group by
  d.project_id,
  d.repository_source,
  t.time_interval
