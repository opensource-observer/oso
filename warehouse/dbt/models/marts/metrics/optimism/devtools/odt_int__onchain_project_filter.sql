{% set min_transaction_threshold = 1000 %}

with filtered_transactions as (
  select
    project_id,
    event_source,
    transaction_count_6_months as amount
  from {{ ref('onchain_metrics_by_project_v1') }}
  where event_source in ('OPTIMISM', 'BASE', 'MODE', 'ZORA', 'METAL', 'FRAX')
),

aggregated_transactions as (
  select
    project_id,
    sum(amount) as total_amount
  from filtered_transactions
  group by project_id
),

eligible_projects as (
  select project_id
  from aggregated_transactions
  where total_amount >= {{ min_transaction_threshold }}
)

select
  txns.project_id,
  projects.project_name,
  projects.display_name,
  txns.event_source,
  txns.amount
from filtered_transactions as txns
inner join {{ ref('projects_v1') }} as projects
  on txns.project_id = projects.project_id
where txns.project_id in (select project_id from eligible_projects)
order by projects.project_name
