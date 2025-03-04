model(name oso.stg_op_atlas_project_links, dialect trino, kind full,)
;

with
    latest_links as (
        select
            *,
            row_number() over (
                partition by project_id, url order by updated_at desc
            ) as rn
        from @oso_source('bigquery.op_atlas.project_links')
    )

select
    -- Translating op-atlas project_id to OSO project_id
    @oso_id('OP_ATLAS', project_id) as project_id,
    id as artifact_source_id,
    'WWW' as artifact_source,
    null::text as artifact_namespace,
    url as artifact_name,
    url as artifact_url,
    'WEBSITE' as artifact_type,
    name as display_name,
    description,
    created_at,
    updated_at
from latest_links
where rn = 1
