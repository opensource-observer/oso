with repos as (
  select
    a.application_id,
    a.project_name,
    a.artifact,
    (r.application_id is not null) as has_contracts
  from {{ source('static_data_sources', 'agora_rf4_artifacts_by_app') }} as a
  left join
    {{ source('static_data_sources', 'agora_rf4_repos_with_contracts') }} as r
    on a.artifact = r.artifact
  where a.artifact_source = 'GITHUB'
),

repos_w_contracts_by_app as (
  select
    application_id,
    max(has_contracts) as has_contracts
  from repos
  group by application_id
),

repos_by_app as (
  select
    repos.application_id,
    repos.project_name,
    repos.artifact,
    repos.has_contracts,
    (
      repos.has_contracts = true
      or repos_w_contracts_by_app.has_contracts = false
    ) as scan
  from repos
  inner join repos_w_contracts_by_app
    on repos.application_id = repos_w_contracts_by_app.application_id
)

select distinct
  application_id,
  project_name,
  artifact as url,
  has_contracts,
  scan,
  lower(replace(artifact, 'https://github.com/', '')) as repo
from repos_by_app
