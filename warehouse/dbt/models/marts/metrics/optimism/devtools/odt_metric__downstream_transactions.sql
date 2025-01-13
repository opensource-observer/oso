with devtool_to_onchain as (
  select distinct
    devtool_project_id,
    onchain_project_id
  from {{ ref('odt_int__devtool_to_onchain_project_registry') }}
  where edge_type in (
    'npm_package',
    'rust_package',
    'developer_connection',
    'solidity_developer_connection'
  )
),

project_contracts as (
  select
    project_id,
    artifact_id
  from {{ ref('artifacts_by_project_v1') }}
  where artifact_source in (
    'OPTIMISM', 'BASE', 'MODE', 'ZORA', 'METAL', 'FRAX'
  )
  and artifact_id not in (
    select artifact_id
    from {{ ref('int_artifacts_in_ossd_by_project') }}
    where artifact_type = 'WALLET'
  )
  and project_id in (select onchain_project_id from devtool_to_onchain)
),

downstream_transactions as (
  select
    d2o.devtool_project_id,
    txns.to_artifact_id,
    sum(txns.amount) as total_transactions
  from {{ ref('int_superchain_transactions') }} as txns
  inner join project_contracts as pc
    on txns.to_artifact_id = pc.artifact_id
  inner join devtool_to_onchain as d2o
    on pc.project_id = d2o.onchain_project_id
  group by
    d2o.devtool_project_id,
    txns.to_artifact_id
)

select
  devtool_project_id as project_id,
  'downstream_transactions' as metric,
  sum(total_transactions) as amount
from downstream_transactions
group by devtool_project_id
