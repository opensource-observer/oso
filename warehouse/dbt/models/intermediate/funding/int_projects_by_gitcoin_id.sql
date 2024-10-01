with gitcoin_projects as (
  select distinct
    pg.gitcoin_group_id,
    pg.latest_project_github,
    pg.latest_project_recipient_address,
    project_lookup.gitcoin_project_id
  from {{ ref('stg_gitcoin__project_groups') }} as pg
  left join {{ ref('stg_gitcoin__project_lookup') }} as project_lookup
    on pg.gitcoin_group_id = project_lookup.gitcoin_group_id
  where not (
    not regexp_contains(pg.latest_project_github, '^[a-zA-Z0-9_-]+$')
    or pg.latest_project_github like '%?%'
    or pg.latest_project_github = 'none'
    or length(pg.latest_project_github) > 39
  )
),

oso_projects as (
  select distinct
    wallets.project_id as oso_project_id,
    wallets.artifact_name as address,
    repos.artifact_namespace as repo_owner
  from {{ ref('int_artifacts_in_ossd_by_project') }} as wallets
  cross join {{ ref('int_artifacts_in_ossd_by_project') }} as repos
  where
    wallets.artifact_type = 'WALLET'
    and repos.artifact_source = 'GITHUB'
    and wallets.project_id = repos.project_id
)

select distinct
  gitcoin_projects.gitcoin_group_id,
  gitcoin_projects.gitcoin_project_id,
  oso_projects.oso_project_id
from gitcoin_projects
inner join oso_projects on (
  gitcoin_projects.latest_project_github = oso_projects.repo_owner
  and gitcoin_projects.latest_project_recipient_address = oso_projects.address
)
