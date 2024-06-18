{# 
  All impact metrics, grouped by project
#}

with metrics as (
  select * from {{ ref('rf4_check_oss_requirements') }}
  union all
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
  select * from {{ ref('rf4_daily_active_addresses') }}
  union all
  select * from {{ ref('rf4_trusted_monthly_active_users') }}
  union all
  select * from {{ ref('rf4_monthly_active_addresses') }}
  union all
  select * from {{ ref('rf4_trusted_users_onboarded') }}
  union all
  select * from {{ ref('rf4_trusted_recurring_users') }}
  union all
  select * from {{ ref('rf4_recurring_addresses') }}
  union all
  select * from {{ ref('rf4_power_user_addresses') }}
  union all
  select * from {{ ref('rf4_openrank_trusted_users') }}
),

pivot_metrics as (
  select
    project_id,
    MAX(
      case when metric = 'check_oss_requirements' then amount else 0 end
    ) as check_oss_requirements,
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
      case when metric = 'daily_active_addresses' then amount else 0 end
    ) as daily_active_addresses,
    MAX(
      case when metric = 'trusted_monthly_active_users' then amount else 0 end
    ) as trusted_monthly_active_users,
    MAX(
      case when metric = 'monthly_active_addresses' then amount else 0 end
    ) as monthly_active_addresses,
    MAX(
      case when metric = 'trusted_recurring_users' then amount else 0 end
    ) as trusted_recurring_users,
    MAX(
      case when metric = 'recurring_addresses' then amount else 0 end
    ) as recurring_addresses,
    MAX(
      case when metric = 'power_user_addresses' then amount else 0 end
    ) as power_user_addresses,
    MAX(
      case when metric = 'openrank_trusted_users_count' then amount else 0 end
    ) as openrank_trusted_users_count
  from metrics
  group by project_id
)

select
  agora_rf4_to_ossd.application_id,
  agora_rf4_to_ossd.oso_project_name,
  pivot_metrics.check_oss_requirements,
  pivot_metrics.gas_fees,
  pivot_metrics.transaction_count,
  pivot_metrics.trusted_transaction_count,
  pivot_metrics.trusted_transaction_share,
  pivot_metrics.trusted_users_onboarded,
  pivot_metrics.daily_active_addresses,
  pivot_metrics.trusted_daily_active_users,
  pivot_metrics.monthly_active_addresses,
  pivot_metrics.trusted_monthly_active_users,
  pivot_metrics.recurring_addresses,
  pivot_metrics.trusted_recurring_users,
  pivot_metrics.power_user_addresses,
  pivot_metrics.openrank_trusted_users_count
from pivot_metrics
left join {{ ref('projects_v1') }}
  on pivot_metrics.project_id = projects_v1.project_id
left join {{ source("static_data_sources", "agora_rf4_to_ossd") }}
  on projects_v1.project_name = agora_rf4_to_ossd.oso_project_name
where agora_rf4_to_ossd.application_id is not null
