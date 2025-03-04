MODEL (
  name metrics.stg_op_atlas_project_website,
  dialect trino,
  kind FULL,
);

select
    -- Translating op-atlas project_id to OSO project_id
    @oso_id('OP_ATLAS', projects.id) as project_id,
    websites._dlt_id as artifact_source_id,
    'WWW' as artifact_source,
    'WWW' as artifact_namespace,
    websites.value as artifact_name,
    websites.value as artifact_url,
    'WEBSITE' as artifact_type
from @oso_source('bigquery.op_atlas.project__website') as websites
left join @oso_source('bigquery.op_atlas.project') as projects
on websites._dlt_parent_id = projects._dlt_id