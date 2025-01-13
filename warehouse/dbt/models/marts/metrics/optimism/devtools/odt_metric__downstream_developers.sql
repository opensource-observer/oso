{% set trailing_months = 6 %}

with devtool_to_onchain as (
  select distinct
    devtool_project_id,
    onchain_artifact_id
  from {{ ref('odt_int__devtool_to_onchain_project_registry') }}
  where edge_type in (
    'npm_package',
    'rust_package',
    'developer_connection',
    'solidity_developer_connection'
  )
),

developer_edges as (
  select distinct
    from_artifact_id as developer_id,
    to_artifact_id as onchain_artifact_id
  from {{ ref('int_events__github') }}
  where
    event_type = 'COMMIT_CODE'
    and date(time) >= date_sub(
      current_date(), interval {{ trailing_months }} month
    )
),

downstream_developers as (
  select
    de.developer_id,
    d2o.devtool_project_id,
    de.onchain_artifact_id
  from developer_edges as de
  inner join devtool_to_onchain as d2o
    on de.onchain_artifact_id = d2o.onchain_artifact_id
)

select
  devtool_project_id as project_id,
  'downstream_developers' as metric,
  count(distinct developer_id) as amount
from downstream_developers
group by devtool_project_id
