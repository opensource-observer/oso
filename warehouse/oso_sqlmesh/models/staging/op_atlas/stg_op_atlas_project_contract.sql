model(name oso.stg_op_atlas_project_contract, dialect trino, kind full,)
;

with
    latest_contracts as (
        select
            *,
            row_number() over (
                partition by project_id, chain_id, contract_address
                order by updated_at desc
            ) as rn
        from @oso_source('bigquery.op_atlas.project_contract')
    )

select
    -- Translating op-atlas project_id to OSO project_id
    @oso_id('OP_ATLAS', project_id) as project_id,
    id as artifact_source_id,
    @chain_id_to_chain_name(chain_id) as artifact_source,
    null::text as artifact_namespace,
    contract_address as artifact_name,
    null::text as artifact_url,
    'CONTRACT' as artifact_type
from latest_contracts
where rn = 1
