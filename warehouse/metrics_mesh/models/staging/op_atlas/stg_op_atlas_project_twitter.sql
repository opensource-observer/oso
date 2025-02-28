MODEL (
  name metrics.stg_op_atlas_project_twitter,
  dialect trino,
  kind FULL,
);

with sanitized as (
    select
        projects.project_id,
        projects.project_source_id as artifact_source_id,
        'TWITTER' as artifact_source,
        'TWITTER' as artifact_namespace,
        case
            when
                projects.twitter like 'https://twitter.com/%'
                then SUBSTR(projects.twitter, 21)
            when
                projects.twitter like 'https://x.com/%'
                then SUBSTR(projects.twitter, 15)
            when 
                projects.twitter like '@%'
                then SUBSTR(projects.twitter, 2)
            else projects.twitter
        end as artifact_name
    from metrics.stg_op_atlas_project as projects
)

select
  project_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  'SOCIAL_HANDLE' as artifact_type,
  concat('https://x.com/', artifact_name) as artifact_url,
from sanitized