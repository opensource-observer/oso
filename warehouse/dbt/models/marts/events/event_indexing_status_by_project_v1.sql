{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  events.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name,
  events.event_source as `event_source`,
  events.event_type,
  MIN(events.bucket_day) as first_event_date,
  MAX(events.bucket_day) as last_event_date,
  COUNT(distinct events.bucket_day) as eventful_day_count
from {{ ref('events_daily_to_project_by_source') }} as events
inner join {{ ref('projects_v1') }} as projects
  on events.project_id = projects.project_id
group by
  events.project_id,
  projects.project_source,
  projects.project_namespace,
  projects.project_name,
  events.event_source,
  events.event_type
