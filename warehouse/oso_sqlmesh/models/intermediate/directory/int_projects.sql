MODEL (
  name metrics.int_projects,
  description 'All projects',
  kind FULL
);

with ossd_projects as (
  select
    project_id,
    project_source,
    project_namespace,
    project_name,
    display_name,
    description,
    --ARRAY_LENGTH(github) as github_artifact_count,
    --ARRAY_LENGTH(blockchain) as blockchain_artifact_count,
    --ARRAY_LENGTH(npm) as npm_artifact_count
  from metrics.stg_ossd__current_projects
),

op_atlas_projects as (
  select
    project_id,
    project_source,
    project_namespace,
    project_name,
    display_name,
    description
  from metrics.stg_op_atlas_project
)

select * from ossd_projects
union all
select * from op_atlas_projects