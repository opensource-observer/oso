MODEL (
  name metrics.stg_ossd__missing_sbom,
  description 'The most recent view of sboms from the ossd dagster source',
  dialect trino,
  kind VIEW,
);

with all_repos as (
  select *
  from @oso_source('bigquery.ossd.repositories')
),

all_ossd as (
  select *
  from @oso_source('bigquery.ossd.sbom')
  where
    artifact_source = 'GITHUB'
)

select
  owner as artifact_namespace,
  name as artifact_name,
  'GITHUB' as artifact_source,
  url as artifact_url,
  ingestion_time as snapshot_at
from
  all_repos as ar
left join
  all_ossd as ao
  on
    CONCAT(ao.artifact_namespace, '/', ao.artifact_name) = ar.name_with_owner
where
  ao.artifact_namespace is null
