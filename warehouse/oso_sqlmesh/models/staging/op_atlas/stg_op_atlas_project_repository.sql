model(name oso.stg_op_atlas_project_repository, dialect trino, kind full,)
;

with
    latest_repositories as (
        select
            *,
            row_number() over (
                partition by project_id, url order by updated_at desc
            ) as rn
        from @oso_source('bigquery.op_atlas.project_repository')
        where verified = true and upper(type) = 'GITHUB'
    )

select
    -- Translating op-atlas project_id to OSO project_id
    @oso_id('OP_ATLAS', repos.project_id) as project_id,
    repos.id as artifact_source_id,
    'GITHUB' as artifact_source,
    @url_parts(repos.url, 2) as artifact_namespace,
    @url_parts(repos.url, 3) as artifact_name,
    repos.url as artifact_url,
    'REPOSITORY' as artifact_type,
-- repos.created_at,
-- repos.updated_at,
-- repos.verified as is_verified,
-- repos.open_source as is_open_source,
-- repos.contains_contracts,
-- repos.crate as contains_crates,
-- repos.npm_package as contains_npm
from latest_repositories as repos
where rn = 1
