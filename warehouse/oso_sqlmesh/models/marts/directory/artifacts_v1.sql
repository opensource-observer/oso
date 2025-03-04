model(name oso.artifacts_v1, kind full, tags('export'),)
;

select
    artifact_id, artifact_source_id, artifact_source, artifact_namespace, artifact_name,
from oso.int_artifacts
