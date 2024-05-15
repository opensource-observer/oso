{# 
  All impact metrics, grouped by project
#}

with metrics as (
  select * from {{ ref('rf4_gas_fees') }}
  union all
  select * from {{ ref('rf4_transactions') }}
  union all
  select * from {{ ref('rf4_trusted_transactions') }}
  union all
  select * from {{ ref('rf4_trusted_users_share_of_transactions') }}
  union all
  select * from {{ ref('rf4_trusted_daily_active_users') }}
  union all
  select * from {{ ref('rf4_trusted_monthly_active_users') }}
  union all
  select * from {{ ref('rf4_trusted_users_onboarded') }}
  union all
  select * from {{ ref('rf4_trusted_recurring_users') }}
),

pivot_metrics as (
  select
    project_id,
    MAX(
      case when metric = 'gas_fees' then amount else 0 end
    ) as gas_fees,
    MAX(
      case when metric = 'transaction_count' then amount else 0 end
    ) as transaction_count,
    MAX(
      case when metric = 'trusted_transaction_count' then amount else 0 end
    ) as trusted_transaction_count,
    MAX(
      case when metric = 'trusted_transaction_share' then amount else 0 end
    ) as trusted_transaction_share,
    MAX(
      case when metric = 'trusted_users_onboarded' then amount else 0 end
    ) as trusted_users_onboarded,
    MAX(
      case when metric = 'trusted_daily_active_users' then amount else 0 end
    ) as trusted_daily_active_users,
    MAX(
      case when metric = 'trusted_monthly_active_users' then amount else 0 end
    ) as trusted_monthly_active_users,
    MAX(
      case when metric = 'trusted_recurring_users' then amount else 0 end
    ) as trusted_recurring_users
  from metrics
  group by project_id
)

select
  pivot_metrics.*,
  projects_v1.project_name
from pivot_metrics
left join {{ ref('projects_v1') }}
  on pivot_metrics.project_id = projects_v1.project_id
