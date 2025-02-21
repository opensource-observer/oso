MODEL (
  name metrics.stg_op_atlas_project_farcaster,
  dialect trino,
  kind FULL,
);

select
    -- Translating op-atlas project_id to OSO project_id
    @oso_id('OP_ATLAS', projects.id) as project_id,
    farcaster._dlt_id as artifact_source_id,
    'FARCASTER' as artifact_source,
    'FARCASTER' as artifact_namespace,
    -- Right now they don't validate
    -- so the value can either be a handle or URL
    farcaster.value as artifact_name,
    concat('https://warpcast.com/', farcaster.value) as artifact_url,
    'SOCIAL_HANDLE' as artifact_type
from @oso_source('bigquery.op_atlas.project__farcaster') as farcaster
left join @oso_source('bigquery.op_atlas.project') as projects
on farcaster._dlt_parent_id = projects._dlt_id