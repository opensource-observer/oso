{# 
  TODO: this should go into a yml file for doc generation
  Summary onchain metrics for a project:
    - project_id: The unique identifier for the project
    - network: The network the project is deployed on
    - num_contracts: The number of contracts in the project
    - first_txn_date: The date of the first transaction to the project
    - total_txns: The total number of transactions to the project
    - total_l2_gas: The total L2 gas used by the project
    - total_users: The number of unique users interacting with the project    
    - txns_6_months: The total number of transactions to the project in the last 6 months
    - l2_gas_6_months: The total L2 gas used by the project in the last 6 months
    - users_6_months: The number of unique users interacting with the project in the last 6 months
    - new_users: The number of users interacting with the project for the first time in the last 3 months
    - active_users: The number of active users interacting with the project in the last 3 months
    - high_frequency_users: The number of users who have made 1000+ transactions with the project in the last 3 months
    - more_active_users: The number of users who have made 10-999 transactions with the project in the last 3 months
    - less_active_users: The number of users who have made 1-9 transactions with the project in the last 3 months
    - multi_project_users: The number of users who have interacted with 3+ projects in the last 3 months
#}
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
  date_first_txn as `first_transaction_date`,
  total_txns as `transaction_count_all`,
  txns_6_months as `transaction_count_6_months`,
  total_l2_gas as `l2_gas_sum_all`,
  l2_gas_6_months as `l2_gas_sum_6_months`,
  total_addresses as `address_count_all`,
  new_addresses as `new_address_count_3_months`,
  returning_addresses as `returning_address_count_3_months`,
  high_activity_addresses as `high_activity_address_count_3_months`,
  med_activity_addresses as `medium_activity_address_count_3_months`,
  low_activity_addresses as `low_activity_address_count_3_months`,
  --multi_project_addresses as `multi_project_address_count_3_months`,
  (new_addresses + returning_addresses) as `address_count_3_months`
from {{ ref('int_onchain_metrics_by_project') }}
