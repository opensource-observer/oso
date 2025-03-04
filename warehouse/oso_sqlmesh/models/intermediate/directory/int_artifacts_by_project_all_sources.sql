MODEL (
  name metrics.int_artifacts_by_project_all_sources,
  kind FULL,
  dialect trino
);

with unioned as (
  select
    project_id,
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  from metrics.int_artifacts_by_project_in_ossd
  union all
  select
    project_id,
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  from metrics.int_artifacts_by_project_in_op_atlas
)

select distinct
  projects.project_source,
  projects.project_namespace,
  projects.project_name,
  unioned.*
from unioned
join metrics.int_projects as projects
  on unioned.project_id = projects.project_id
