model(name oso.artifacts_by_project_v1, kind full, tags('export'),)
;

select
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    project_id,
    project_source,
    project_namespace,
    project_name
from oso.int_artifacts_by_project
