{# 
  The most recent view of grants to projects from the oss-funding source.
#}

{% set oss_funding_url = "https://github.com/opensource-observer/oss-funding" %}

with grants as (
  select -- noqa: ST06
    CAST(funding_date as timestamp) as `time`,
    'GRANT_RECEIVED_USD' as event_type,
    COALESCE(project_url, '{{ oss_funding_url }}') as event_source_id,
    'OSS_FUNDING' as event_source,
    LOWER(project_name) as project_name,
    case
      when funder_name in ('Optimism Foundation') then 'op'
      when funder_name in ('Arbitrum Foundation') then 'arbitrumfoundation'
      when funder_name in ('Octant') then 'octant-golemfoundation'
      when funder_name in ('Gitcoin Grants') then 'gitcoin'
      when funder_name in ('DAO Drops (dOrg)') then 'dao-drops-dorgtech'
    end as funder_name,
    LOWER(project_address) as to_name,
    case
      when funding_network in ('mainnet', '1.0') then 'ethereum'
      when funding_network in ('optimism', '10.0') then 'optimism'
      when funding_network in ('arbitrum', '42161.0') then 'arbitrum_one'
      when funding_network in ('pgn', '424.0') then 'pgn'
      when funding_network in ('polygon', '137.0') then 'polygon'
      else 'other'
    end as to_namespace,
    'WALLET' as to_type,
    LOWER(project_address) as to_artifact_source_id,
    LOWER(funder_address) as from_name,
    case
      when funding_network in ('mainnet', '1.0') then 'ethereum'
      when funding_network in ('optimism', '10.0') then 'optimism'
      when funding_network in ('arbitrum', '42161.0') then 'arbitrum_one'
      when funding_network in ('pgn', '424.0') then 'pgn'
      when funding_network in ('polygon', '137.0') then 'polygon'
      else 'other'
    end as from_namespace,
    'WALLET' as from_type,
    LOWER(funder_address) as from_artifact_source_id,
    funding_usd as amount
  from {{ source('static_data_sources', 'oss_funding') }}
)

select
  grants.time,
  grants.event_type,
  grants.event_source_id,
  grants.event_source,
  grants.project_name as to_project_name,
  to_projects.project_id as to_project_id,
  grants.to_name,
  grants.to_namespace,
  grants.to_type,
  grants.to_artifact_source_id,
  grants.funder_name as from_project_name,
  from_projects.project_id as from_project_id,
  grants.from_name,
  grants.from_namespace,
  grants.from_type,
  grants.from_artifact_source_id,
  grants.amount
from grants
inner join {{ ref('projects_v1') }} as to_projects
  on grants.project_name = to_projects.project_name
inner join {{ ref('projects_v1') }} as from_projects
  on grants.funder_name = from_projects.project_name
