{{
  config(
    materialized='table',
    partition_by={
      "field": "txn_date",
      "data_type": "timestamp",
      "granularity": "day",
    }
  )
}}

with all_txns as (
  select
    txn_date,
    from_address,
    to_address,
    network
  from {{ ref('rf4_transactions_window') }}
),

contracts as (
  select distinct
    application_id,
    contract_address,
    network
  from {{ ref('rf4_contracts_by_app') }}
)

select
  contracts.application_id,
  all_txns.txn_date,
  all_txns.from_address,
  all_txns.to_address,
  all_txns.network
from all_txns
left join contracts
  on
    all_txns.to_address = contracts.contract_address
    and all_txns.network = contracts.network
where contracts.application_id is not null
