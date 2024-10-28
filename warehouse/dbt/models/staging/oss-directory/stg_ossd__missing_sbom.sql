{{ config(
    materialized = 'view'
) }}

with all_repos as (
  select *
  from
    `ossd.repositories`
),

all_ossd as (
  select *
  from
    `ossd.sbom`
  where
    artifact_source = 'GITHUB'
)

select
  `owner` as artifact_namespace,
  `name` as artifact_name,
  'GITHUB' as artifact_source,
  `url` as artifact_url,
  ingestion_time as snapshot_at
from
  all_repos ar
left join
  all_ossd ao
  on
    CONCAT(ao.artifact_namespace, "/", ao.artifact_name) = ar.name_with_owner
where
  ao.artifact_namespace is null
