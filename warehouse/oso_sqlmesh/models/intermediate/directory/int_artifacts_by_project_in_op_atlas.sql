model(name oso.int_artifacts_by_project_in_op_atlas, kind full, dialect trino)
;

with
    all_websites as (
        select
            project_id,
            artifact_source_id,
            artifact_source,
            artifact_namespace,
            artifact_name,
            artifact_url,
            artifact_type
        from oso.stg_op_atlas_project_website as sites
    ),

    all_farcaster as (
        select
            project_id,
            artifact_source_id,
            artifact_source,
            artifact_namespace,
            artifact_name,
            artifact_url,
            artifact_type
        from oso.stg_op_atlas_project_farcaster as farcaster
    ),

    all_twitter as (
        select
            project_id,
            artifact_source_id,
            artifact_source,
            artifact_namespace,
            artifact_name,
            artifact_url,
            artifact_type
        from oso.stg_op_atlas_project_twitter as twitter
    ),

    all_repository as (
        select
            project_id,
            artifact_source_id,
            artifact_source,
            artifact_namespace,
            artifact_name,
            artifact_url,
            artifact_type
        from oso.stg_op_atlas_project_repository
    ),

    all_contracts as (
        select
            project_id,
            artifact_source_id,
            artifact_source,
            artifact_namespace,
            artifact_name,
            artifact_url,
            artifact_type
        from oso.stg_op_atlas_project_contract
    ),

    all_deployers as (
        select distinct
            project_id,
            artifact_source_id,
            artifact_source,
            artifact_namespace,
            artifact_name,
            artifact_url,
            artifact_type
        from oso.stg_op_atlas_project_deployer
    ),

    all_defillama as (
        select
            project_id,
            artifact_source_id,
            artifact_source,
            artifact_namespace,
            artifact_name,
            artifact_url,
            artifact_type
        from oso.stg_op_atlas_project_defillama
    ),

    all_artifacts as (
        select *
        from all_websites
        union all
        select *
        from all_farcaster
        union all
        select *
        from all_twitter
        union all
        select *
        from all_repository
        union all
        select *
        from all_contracts
        union all
        select *
        from all_deployers
        union all
        select *
        from all_defillama
    ),

    all_normalized_artifacts as (
        select distinct
            project_id,
            lower(artifact_source_id) as artifact_source_id,
            upper(artifact_source) as artifact_source,
            lower(artifact_namespace) as artifact_namespace,
            lower(artifact_name) as artifact_name,
            lower(artifact_url) as artifact_url,
            upper(artifact_type) as artifact_type
        from all_artifacts
    )

select
    project_id,
    @oso_id(artifact_source, artifact_namespace, artifact_name) as artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    artifact_type
from all_normalized_artifacts
