{{
  config(
    materialized='table'
  )
}}

with project_to_developer_graph as (
  select * from {{ ref('int_superchain_s7_project_to_developer_graph') }}
),

project_to_dependency_graph as (
  select * from {{ ref('int_superchain_s7_project_to_dependency_graph') }}
),

-- First create developer overlap relationships
developer_contributions as (
  select
    devtooling_project_id as project_id,
    developer_id,
    timestamp(max(last_event_to_repo)) as last_contribution
  from project_to_developer_graph
  where has_code_contribution = true
  group by devtooling_project_id, developer_id
),

developer_edges as (
  select
    a.project_id as onchain_builder_project_id,
    b.project_id as devtooling_project_id,
    'DEVELOPER_OVERLAP' as edge_type,
    'SHARED_DEVELOPER_COUNT' as weighting_algorithm,
    count(distinct a.developer_id) as edge_weight,
    max(b.last_contribution) as sample_date
  from developer_contributions as a
  inner join developer_contributions as b
    on
      a.developer_id = b.developer_id
      and a.project_id < b.project_id -- Avoid duplicate edges
  group by 1, 2
),

-- Dependency relationships
dependency_edges as (
  select distinct
    dependent_project_id as onchain_builder_project_id,
    dependency_project_id as devtooling_project_id,
    'DEPENDS_ON' as edge_type,
    'PACKAGE_COUNT' as weighting_algorithm,
    count(distinct dependency_artifact_id) as edge_weight,
    max(sample_date) as sample_date
  from project_to_dependency_graph
  group by 1, 2
)

-- Combine all edges
select * from dependency_edges
union all
select * from developer_edges
