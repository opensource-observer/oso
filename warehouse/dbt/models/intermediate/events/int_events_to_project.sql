{# 
  All events to a project
#}

select
  e.*,
  a.project_id
from {{ ref('int_events_with_artifact_id') }} as e
inner join {{ ref('stg_ossd__artifacts_by_project') }} as a
  on
    e.to_source_id = a.artifact_source_id
    and e.to_namespace = a.artifact_namespace
    and e.to_type = a.artifact_type
