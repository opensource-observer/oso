{#
  WIP: Still in Development
  Count the number of transaction from trusted users
#}

select
  e.project_id,
  t.time_interval,
  'TRUSTED_TRANSACTIONS_TOTAL' as impact_metric,
  SUM(e.amount) as amount
from {{ ref('int_events_to_project') }} as e
cross join {{ ref('int_time_intervals') }} as t
where
  DATE(e.time) >= t.start_date
  and e.from_id in (
    select user_id
    from {{ ref('int_users') }}
  )
  and e.event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
group by
  e.project_id,
  t.time_interval
