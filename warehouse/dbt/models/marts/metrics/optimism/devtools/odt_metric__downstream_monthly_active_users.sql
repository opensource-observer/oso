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
  where project_id in (select onchain_project_id from devtool_to_onchain)
),

downstream_maus as (
  select
    d2o.devtool_project_id,
    txns.to_artifact_id,
    date_trunc(txns.time, month) as month, -- TODO: this should be rolling
    count(distinct txns.from_artifact_id) as active_users
  from {{ ref('int_superchain_transactions') }} as txns
  inner join project_contracts as pc
    on txns.to_artifact_id = pc.artifact_id
  inner join devtool_to_onchain as d2o
    on pc.project_id = d2o.onchain_project_id
  group by
    d2o.devtool_project_id,
    txns.to_artifact_id,
    date_trunc(txns.time, month)
)

select
  devtool_project_id as project_id,
  'downstream_monthly_active_users' as metric,
  avg(active_users) as amount -- TODO: this should be rolling
from downstream_maus
group by devtool_project_id
