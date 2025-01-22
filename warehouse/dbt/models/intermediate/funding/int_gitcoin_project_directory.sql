with gitcoin_projects as (
  select distinct
    pg.latest_project_github,
    pg.latest_project_recipient_address,
    project_lookup.gitcoin_project_id,
    not(
      not regexp_contains(pg.latest_project_github, '^[a-zA-Z0-9_-]+$')
      or pg.latest_project_github like '%?%'
      or pg.latest_project_github = 'none'
      or length(pg.latest_project_github) > 39
    ) as is_valid_github
  from {{ ref('stg_gitcoin__project_groups') }} as pg
  left join {{ ref('stg_gitcoin__project_lookup') }} as project_lookup
    on pg.gitcoin_group_id = project_lookup.gitcoin_group_id
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
),

wallet_matches as (
  select distinct
    gitcoin_projects.gitcoin_project_id,
    gitcoin_projects.latest_project_github,
    gitcoin_projects.latest_project_recipient_address,
    oso_projects.oso_project_id as oso_wallet_match
  from gitcoin_projects
  left join oso_projects
    on gitcoin_projects.latest_project_recipient_address = oso_projects.address
),

repo_matches as (
  select distinct
    wm.*,
    oso_projects.oso_project_id as oso_repo_match
  from wallet_matches as wm
  left join oso_projects
    on wm.latest_project_github = oso_projects.repo_owner
),

final_matches as (
  select distinct
    gitcoin_projects.gitcoin_project_id,
    gitcoin_projects.latest_project_github,
    gitcoin_projects.latest_project_recipient_address,
    repo_matches.oso_wallet_match,
    repo_matches.oso_repo_match,
    case
      when repo_matches.oso_wallet_match is not null
        then repo_matches.oso_wallet_match
      when
        repo_matches.oso_repo_match is not null
        and gitcoin_projects.is_valid_github
        then repo_matches.oso_repo_match
    end as oso_project_id
  from repo_matches
  left join gitcoin_projects
    on repo_matches.gitcoin_project_id = gitcoin_projects.gitcoin_project_id
)

select
  gp.gitcoin_project_id,
  gp.latest_project_github,
  gp.latest_project_recipient_address,
  fm.oso_wallet_match,
  fm.oso_repo_match,
  fm.oso_project_id,
  projects.project_name as oso_project_name,
  projects.display_name as oso_display_name
from gitcoin_projects as gp
left join final_matches as fm
  on gp.gitcoin_project_id = fm.gitcoin_project_id
left join {{ ref('projects_v1') }} as projects
  on fm.oso_project_id = projects.project_id
