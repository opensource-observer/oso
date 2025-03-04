MODEL (
  name metrics.stg_op_atlas_project_defillama,
  dialect trino,
  kind FULL,
);

select
    -- Translating op-atlas project_id to OSO project_id
    @oso_id('OP_ATLAS', projects.id) as project_id,
    defillama._dlt_id as artifact_source_id,
    'DEFILLAMA' as artifact_source,
    'DEFILLAMA' as artifact_namespace,
    defillama.value as artifact_name,
    concat('https://defillama.com/protocol/', defillama.value) as artifact_url,
    'DEFILLAMA' as artifact_type
from @oso_source('bigquery.op_atlas.project__defi_llama_slug') as defillama
left join @oso_source('bigquery.op_atlas.project') as projects
on defillama._dlt_parent_id = projects._dlt_id