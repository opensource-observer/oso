{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  e.event_type,
  e.project_id,
  e.from_id as artifact_id,
  MIN(e.time) as event_time
from {{ ref('int_events_to_project') }} as e
group by e.event_type, e.project_id, e.from_id
