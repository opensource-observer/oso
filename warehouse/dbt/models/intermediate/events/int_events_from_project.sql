{# 
  All events from a project
#}

select
  e.*,
  a.project_id
from {{ ref('int_events_with_artifact_id') }} as e
left join {{ ref('stg_ossd__artifacts_by_project') }} as a
  on
    e.from_source_id = a.artifact_source_id
    and e.from_namespace = a.artifact_namespace
    and e.from_type = a.artifact_type
