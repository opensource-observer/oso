{{ 
  config(meta = {
    'sync_to_db': False
  }) 
}}

with metrics as (
  select * from {{ ref('int_onchain_metric__active_addresses') }}
  union all
  select * from {{ ref('int_onchain_metric__active_contracts') }}
  union all
  select * from {{ ref('int_onchain_metric__gas_fees') }}
  union all
  select *
  from {{ ref('int_onchain_metric__high_low_activity_addresses') }}
  union all
  select *
  from {{ ref('int_onchain_metric__multi_project_addresses') }}
  union all
  select *
  from {{ ref('int_onchain_metric__new_addresses') }}
  union all
  select *
  from {{ ref('int_onchain_metric__returning_addresses') }}
  union all
  select * from {{ ref('int_onchain_metric__transactions') }}
),

aggs as (
  select
    project_id,
    network,
    SUM(
      case
        when
          metric = 'active_contract_count'
          and time_interval = '90 DAYS'
          then amount
        else 0
      end
    ) as contract_count,
    SUM(
      case
        when
          metric = 'transaction_count'
          and time_interval = 'ALL'
          then amount
        else 0
      end
    ) as transaction_count,
    SUM(
      case
        when
          metric = 'gas_fees'
          and time_interval = 'ALL'
          then amount
        else 0
      end
    ) as total_l2_gas,
    SUM(
      case
        when
          metric = 'address_count'
          and time_interval = 'ALL'
          then amount
        else 0
      end
    ) as total_addresses,
    SUM(
      case
        when
          metric = 'new_address_count'
          and time_interval = '90 DAYS'
          then amount
        else 0
      end
    ) as new_addresses,
    SUM(
      case
        when
          metric = 'returning_address_count'
          and time_interval = '90 DAYS'
          then amount
        else 0
      end
    ) as returning_addresses,
    SUM(
      case
        when
          metric = 'high_activity_address_count'
          and time_interval = '90 DAYS'
          then amount
        else 0
      end
    ) as high_activity_addresses,
    SUM(
      case
        when
          metric = 'medium_activity_address_count'
          and time_interval = '90 DAYS'
          then amount
        else 0
      end
    ) as medium_activity_addresses,
    SUM(
      case
        when
          metric = 'low_activity_address_count'
          and time_interval = '90 DAYS'
          then amount
        else 0
      end
    ) as low_activity_addresses,
    SUM(
      case
        when
          metric = 'multi_project_address_count'
          and time_interval = '90 DAYS'
          then amount
        else 0
      end
    ) as multi_project_addresses
  from metrics
  group by
    project_id,
    network
)

select
  aggs.* except (project_id),
  p.project_source,
  p.project_namespace,
  p.project_name,
  p.project_id
from
  {{ ref('projects_v1') }} as p
left join aggs
  on p.project_id = aggs.project_id
