model(name oso.stg_op_atlas_project, dialect trino, kind full,)
;

select
    @oso_id('OP_ATLAS', id)::text as project_id,
    id::text as project_source_id,
    'OP_ATLAS' as project_source,
    null::text as project_namespace,
    id::text as project_name,
    name::text as display_name,
    description::text,
    category::text,
    thumbnail_url::text,
    banner_url::text,
    twitter::text,
    mirror::text,
    open_source_observer_slug::text,
    created_at::timestamp,
    updated_at::timestamp,
    deleted_at::timestamp,
from @oso_source('bigquery.op_atlas.project')
