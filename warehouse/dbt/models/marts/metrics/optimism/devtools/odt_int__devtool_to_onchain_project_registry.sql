with code_deps as (
  select distinct
    dependency_project_id as devtool_project_id,
    dependency_artifact_id as devtool_artifact_id,
    dependent_project_id as onchain_project_id,
    concat(lower(dependency_source), '_', 'package') as edge_type
  from {{ ref('odt_int__code_dependencies') }}
),

dev_deps as (
  select distinct
    other_project_id as devtool_project_id,
    other_artifact_id as devtool_artifact_id,
    onchain_project_id as onchain_project_id,
    'developer_connection' as edge_type
  from {{ ref('odt_int__developer_relationships') }}
),

solidity_dev_deps as (
  select distinct
    other_project_id as devtool_project_id,
    other_artifact_id as devtool_artifact_id,
    onchain_project_id as onchain_project_id,
    'solidity_developer_connection' as edge_type
  from {{ ref('odt_int__developer_relationships') }}
  where is_solidity_developer = true
)

select * from code_deps
union all
select * from dev_deps
union all
select * from solidity_dev_deps
