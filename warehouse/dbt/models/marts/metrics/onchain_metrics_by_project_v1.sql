{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  project_id,
  project_source,
  project_namespace,
  project_name,
  display_name,
  event_source,
  days_since_first_transaction,
  active_contract_count_90_days,
  transaction_count,
  transaction_count_6_months,
  gas_fees_sum,
  gas_fees_sum_6_months,
  address_count,
  address_count_90_days,
  new_address_count_90_days,
  returning_address_count_90_days,
  high_activity_address_count_90_days,
  medium_activity_address_count_90_days,
  low_activity_address_count_90_days,
  multi_project_address_count_90_days
from {{ ref('int_onchain_metrics_by_project') }}
