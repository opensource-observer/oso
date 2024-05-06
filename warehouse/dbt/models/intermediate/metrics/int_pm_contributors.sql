{# 
  
#}

select
  d.project_id,
  t.time_interval,
  CONCAT('CONTRIBUTORS_TOTAL') as impact_metric,
  COUNT(distinct d.from_id) as amount
from {{ ref('int_devs') }} as d
cross join {{ ref('int_time_intervals') }} as t
group by
  d.project_id,
  t.time_interval
