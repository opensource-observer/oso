{{
  config(
    materialized='table'
  )
}}

{# 
  The most recent view of sboms from the ossd dagster source.
#}

with ranked_sboms as (
  select
    artifact_namespace,
    artifact_name,
    artifact_source,
    package,
    package_source,
    package_version,
    snapshot_at,
    ROW_NUMBER()
      over (partition by artifact_namespace, artifact_name, artifact_source, package, package_source order by snapshot_at desc)
      as row_num
  from {{ oso_source('ossd', 'sbom') }}
  where package_source in (
    'NPM',
    'PYPI',
    'GOLANG',
    'CARGO'
  )
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
