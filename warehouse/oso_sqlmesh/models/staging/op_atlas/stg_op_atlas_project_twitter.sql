model(name oso.stg_op_atlas_project_twitter, dialect trino, kind full,)
;

with
    sanitized as (
        select
            projects.project_id,
            projects.project_source_id as artifact_source_id,
            'TWITTER' as artifact_source,
            null::text as artifact_namespace,
            case
                when projects.twitter like 'https://twitter.com/%'
                then substr(projects.twitter, 21)
                when projects.twitter like 'https://x.com/%'
                then substr(projects.twitter, 15)
                when projects.twitter like '@%'
                then substr(projects.twitter, 2)
                else projects.twitter
            end as artifact_name
        from oso.stg_op_atlas_project as projects
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
