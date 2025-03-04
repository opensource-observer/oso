model(name oso.int_artifacts_by_project, kind full)
;

select distinct
    artifacts.artifact_id,
    artifacts.artifact_source_id,
    artifacts.artifact_source,
    artifacts.artifact_namespace,
    artifacts.artifact_name,
    artifacts.artifact_url,
    artifacts.project_id,
    projects.project_source,
    projects.project_namespace,
    projects.project_name
from oso.int_all_artifacts as artifacts
left join oso.int_projects as projects on artifacts.project_id = projects.project_id
where artifacts.project_id is not null
