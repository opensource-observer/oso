model(
  name oso.artifacts_by_user_v1, 
  kind full, 
  tags('export'), 
  enabled false,
  audits (
    not_null(columns := (artifact_id, user_id))
  )
)
;

select
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    user_id,
    user_source_id,
    user_source,
    user_type,
    user_namespace,
    user_name
from oso.int_artifacts_by_user
