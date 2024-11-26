with source as (
  select
    `date`,
    artifact_name,
    downloads
  from {{ source('npm', 'downloads') }}
)

select * from source
