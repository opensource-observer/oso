model(
    name oso.stg_ossd__current_sbom,
    description 'The most recent view of sboms from the ossd dagster source',
    dialect trino,
    kind full,
)
;

with
    ranked_sboms as (
        select
            snapshot_at,
            lower(artifact_namespace) as artifact_namespace,
            lower(artifact_name) as artifact_name,
            upper(artifact_source) as artifact_source,
            lower(package) as package,
            upper(package_source) as package_source,
            lower(package_version) as package_version,
            row_number() over (
                partition by
                    artifact_namespace,
                    artifact_name,
                    artifact_source,
                    package,
                    package_source
                order by snapshot_at desc
            ) as row_num
        from @oso_source('bigquery.ossd.sbom')
    )

select
    artifact_namespace,
    artifact_name,
    artifact_source,
    package,
    package_source,
    package_version,
    snapshot_at
from ranked_sboms
where row_num = 1
