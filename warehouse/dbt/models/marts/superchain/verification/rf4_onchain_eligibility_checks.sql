with projects as (
  select
    app.application_id,
    app.project_name,
    ossd.oso_name as oso_project_name
  from {{ source('static_data_sources', 'agora_rf4_applications') }} as app
  left join
    {{ source('static_data_sources', 'rf4_project_eligibility') }} as ossd
    on app.application_id = ossd.application_id
),

contracts as (
  select
    application_id,
    count(distinct contract_address) as count_linked_addresses
  from {{ ref('rf4_contracts_by_app') }}
  group by application_id
),

txns as (
  select
    application_id,
    txn_date,
    from_address,
    to_address,
    (txn_date > '2023-12-30' and txn_date < '2024-05-02') as txn_in_tight_window
  from {{ ref('rf4_transactions_by_app') }}
)

select
  projects.application_id,
  projects.project_name,
  projects.oso_project_name,
  contracts.count_linked_addresses,
  min(txns.txn_date) as first_transaction,
  count(
    distinct
    case when txns.txn_in_tight_window is true then txns.txn_date end
  ) as num_active_days,
  count(
    distinct
    case when txns.txn_in_tight_window is true then txns.from_address end
  ) as num_unique_addresses_in_tight_window,
  count(distinct txns.from_address) as num_unique_addresses_in_wide_window
from projects
left join contracts on projects.application_id = contracts.application_id
left join txns on projects.application_id = txns.application_id
group by
  projects.application_id,
  projects.project_name,
  projects.oso_project_name,
  contracts.count_linked_addresses
order by
  projects.oso_project_name
