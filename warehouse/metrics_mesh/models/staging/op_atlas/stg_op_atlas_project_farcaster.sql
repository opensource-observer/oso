MODEL (
  name metrics.stg_op_atlas_project_farcaster,
  dialect trino,
  kind FULL,
);

with sanitized as (
  select
      -- Translating op-atlas project_id to OSO project_id
      @oso_id('OP_ATLAS', projects.id) as project_id,
      farcaster._dlt_id as artifact_source_id,
      'FARCASTER' as artifact_source,
      'FARCASTER' as artifact_namespace,
      -- Right now they don't validate
      -- so the value can either be a handle or URL
      case
        when
          farcaster.value like 'https://warpcast.com/%'
          then SUBSTR(farcaster.value, 22)
        when 
          farcaster.value like '/%'
          then SUBSTR(farcaster.value, 2)
        when 
          farcaster.value like '@%'
          then SUBSTR(farcaster.value, 2)
        else farcaster.value
      end as artifact_name,
  from @oso_source('bigquery.op_atlas.project__farcaster') as farcaster
  left join @oso_source('bigquery.op_atlas.project') as projects
  on farcaster._dlt_parent_id = projects._dlt_id
)

select
  project_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  'SOCIAL_HANDLE' as artifact_type,
  concat('https://warpcast.com/', artifact_name) as artifact_url,
from sanitized