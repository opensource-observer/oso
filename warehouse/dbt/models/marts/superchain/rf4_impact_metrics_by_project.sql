{# 
  All impact metrics, grouped by project
#}

with metrics as (
  select * from {{ ref('rf4_gas_fees_by_project') }}
  union all
  select * from {{ ref('rf4_total_transactions_by_project') }}
  union all
  select * from {{ ref('rf4_total_trusted_transactions_by_project') }}
),

pivot_metrics as (
  select
    project_id,
    MAX(case when metric = 'gas_fees' then amount else 0 end) as gas_fees,
    MAX(case when metric = 'transaction_count' then amount else 0 end)
      as transaction_count,
    MAX(case when metric = 'trusted_transaction_count' then amount else 0 end)
      as trusted_transaction_count
  from metrics
  group by project_id
)

select
  pivot_metrics.*,
  projects_v1.project_name
from pivot_metrics
left join {{ ref('projects_v1') }}
  on pivot_metrics.project_id = projects_v1.project_id
