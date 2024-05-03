{# 
  Arbitrum Onchain Metrics
  Summary onchain metrics for a collection:
    - num_projects: The number of projects in the collection
    - num_contracts: The number of contracts in the collection
    - first_txn_date: The date of the first transaction to the collection
    - total_txns: The total number of transactions to the collection
    - total_l2_gas: The total L2 gas used by the collection
    - total_users: The number of unique users interacting with the collection    
    - txns_6_months: The total number of transactions to the collection in the last 6 months
    - l2_gas_6_months: The total L2 gas used by the collection in the last 6 months
    - users_6_months: The number of unique users interacting with the collection in the last 6 months
    - new_users: The number of users interacting with the collection for the first time in the last 3 months
    - active_users: The number of active users interacting with the collection in the last 3 months
    - high_frequency_users: The number of users who have made 1000+ transactions with the collection in the last 3 months
    - more_active_users: The number of users who have made 10-999 transactions with the collection in the last 3 months
    - less_active_users: The number of users who have made 1-9 transactions with the collection in the last 3 months
    - multi_project_users: The number of users who have interacted with 3+ projects in the last 3 months
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

-- CTE for grabbing the onchain transaction data we care about, 
-- including project-collection mapping
with txns as (
  select
    pbc.collection_id,
    c.to_namespace as onchain_network,
    a.project_id,
    c.from_source_id as from_id,
    c.l2_gas,
    c.tx_count,
    DATE(TIMESTAMP_TRUNC(c.time, month)) as bucket_month
  from {{ ref('stg_dune__contract_invocation') }} as c
  inner join {{ ref('stg_ossd__artifacts_by_project') }} as a
    on c.to_source_id = a.artifact_source_id
  inner join {{ ref('stg_ossd__projects_by_collection') }} as pbc
    on a.project_id = pbc.project_id
),

-- CTEs for calculating all-time and 6-month collection metrics across all
-- contracts
metrics_all_time as (
  select
    collection_id,
    onchain_network,
    COUNT(distinct project_id) as total_projects,
    MIN(bucket_month) as first_txn_date,
    COUNT(distinct from_id) as total_users,
    SUM(l2_gas) as total_l2_gas,
    SUM(tx_count) as total_txns
  from txns
  group by collection_id, onchain_network
),

metrics_6_months as (
  select
    collection_id,
    onchain_network,
    COUNT(distinct from_id) as users_6_months,
    SUM(l2_gas) as l2_gas_6_months,
    SUM(tx_count) as txns_6_months
  from txns
  where bucket_month >= DATE_ADD(CURRENT_DATE(), interval -6 month)
  group by collection_id, onchain_network
),

-- CTE for identifying new users to the collection in the last 3 months
new_users as (
  select
    collection_id,
    onchain_network,
    SUM(is_new_user) as new_user_count
  from (
    select
      collection_id,
      onchain_network,
      from_id,
      case
        when
          MIN(bucket_month)
          >= DATE_ADD(CURRENT_DATE(), interval -3 month)
          then 1
        else 0
      end as is_new_user
    from txns
    group by collection_id, onchain_network, from_id
  )
  group by collection_id, onchain_network
),

-- CTEs for segmenting different types of active users based on txn volume at 
-- collection level
user_txns_aggregated as (
  select
    collection_id,
    onchain_network,
    from_id,
    SUM(tx_count) as total_tx_count
  from txns
  where bucket_month >= DATE_ADD(CURRENT_DATE(), interval -3 month)
  group by collection_id, onchain_network, from_id
),

multi_project_users as (
  select
    onchain_network,
    from_id,
    COUNT(distinct project_id) as projects_transacted_on
  from txns
  where bucket_month >= DATE_ADD(CURRENT_DATE(), interval -3 month)
  group by onchain_network, from_id
),

user_segments as (
  select
    collection_id,
    onchain_network,
    COUNT(distinct case
      when user_segment = 'HIGH_FREQUENCY_USER' then from_id
    end) as high_frequency_users,
    COUNT(distinct case
      when user_segment = 'MORE_ACTIVE_USER' then from_id
    end) as more_active_users,
    COUNT(distinct case
      when user_segment = 'LESS_ACTIVE_USER' then from_id
    end) as less_active_users,
    COUNT(distinct case
      when projects_transacted_on >= 3 then from_id
    end) as multi_project_users
  from (
    select
      uta.collection_id,
      uta.onchain_network,
      uta.from_id,
      mpu.projects_transacted_on,
      case
        when uta.total_tx_count >= 1000 then 'HIGH_FREQUENCY_USER'
        when uta.total_tx_count >= 10 then 'MORE_ACTIVE_USER'
        else 'LESS_ACTIVE_USER'
      end as user_segment
    from user_txns_aggregated as uta
    inner join multi_project_users as mpu
      on uta.from_id = mpu.from_id
  )
  group by collection_id, onchain_network
),

-- CTE to count the number of contracts deployed by projects in a collection
contracts as (
  select
    pbc.collection_id,
    a.artifact_namespace as onchain_network,
    COUNT(distinct a.artifact_source_id) as num_contracts
  from {{ ref('stg_ossd__artifacts_by_project') }} as a
  inner join {{ ref('stg_ossd__projects_by_collection') }} as pbc
    on a.project_id = pbc.project_id
  group by pbc.collection_id, onchain_network
),

collection_by_network as (
  select
    c.collection_id,
    c.collection_source,
    c.collection_namespace,
    c.collection_name,
    ctx.onchain_network
  from {{ ref('collections_v1') }} as c
  inner join contracts as ctx
    on c.collection_id = ctx.collection_id
)

-- Final query to join all the metrics together for collections
select
  c.collection_id,
  c.collection_source,
  c.collection_namespace,
  c.collection_name,
  c.onchain_network as `artifact_source`,
  ma.total_projects as `total_project_count`,
  co.num_contracts as `total_contract_count`,
  ma.first_txn_date as `first_transaction_date`,
  ma.total_txns as `total_transaction_count`,
  m6.txns_6_months as `transaction_count_6_months`,
  ma.total_l2_gas,
  m6.l2_gas_6_months,
  ma.total_users as `total_user_address_count`,
  m6.users_6_months as `user_address_count_6_months`,
  nu.new_user_count as `new_user_count_3_months`,
  us.high_frequency_users as `high_frequency_address_count`,
  us.more_active_users as `more_active_user_address_count`,
  us.less_active_users as `less_active_user_address_count`,
  us.multi_project_users as `multi_project_user_address_count`,
  (
    us.high_frequency_users + us.more_active_users + us.less_active_users
  ) as `total_active_user_address_count`
from collection_by_network as c
inner join metrics_all_time as ma
  on
    c.collection_id = ma.collection_id
    and c.onchain_network = ma.onchain_network
inner join metrics_6_months as m6
  on
    c.collection_id = m6.collection_id
    and c.onchain_network = m6.onchain_network
inner join new_users as nu
  on
    c.collection_id = nu.collection_id
    and c.onchain_network = nu.onchain_network
inner join user_segments as us
  on
    c.collection_id = us.collection_id
    and c.onchain_network = us.onchain_network
inner join contracts as co
  on
    c.collection_id = co.collection_id
    and c.onchain_network = co.onchain_network
