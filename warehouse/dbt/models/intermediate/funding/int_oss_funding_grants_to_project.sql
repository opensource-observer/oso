{# 
  The most recent view of grants to projects from the oss-funding source.
#}

{% set oss_funding_url = "https://github.com/opensource-observer/oss-funding" %}

with oss_funding_data as (
  select -- noqa: ST06
    CAST(funding_date as timestamp) as `time`,
    'GRANT_RECEIVED_USD' as event_type,
    '{{ oss_funding_url }}' as event_source_id,
    'OSS_FUNDING' as event_source,
    LOWER(to_project_name) as to_project_name,
    LOWER(from_funder_name) as from_project_name,
    COALESCE(amount,0) as amount
  from {{ source('static_data_sources', 'oss_funding_v1') }}
  where to_project_name is not null
    and from_funder_name is not null
    and amount is not null
),
gitcoin_data as (
  select -- noqa: ST06
    events.event_time as `time`,
    'GRANT_RECEIVED_USD' as event_type,
    case
      when events.transaction_hash is not null then events.transaction_hash
      else CAST(events.gitcoin_project_id as STRING)
    end as event_source_id,
    concat('GITCOIN', '_', funding_type) as event_source,
    projects.project_name as to_project_name,
    'gitcoin' as from_project_name,
    events.amount_in_usd as amount
  from {{ ref('int_gitcoin_funding_events') }} as events
  inner join {{ ref('int_gitcoin_project_directory') }} as project_directory
    on events.gitcoin_project_id = project_directory.gitcoin_project_id
  inner join {{ ref('projects_v1') }} as projects
    on project_directory.oso_project_id = projects.project_id
),
grants as (
  select distinct
    oss_funding_data.time,
    oss_funding_data.event_type,
    oss_funding_data.event_source_id,
    oss_funding_data.event_source,
    oss_funding_data.to_project_name,
    oss_funding_data.from_project_name,
    oss_funding_data.amount
  from oss_funding_data

  union all

  select distinct
    gitcoin_data.time,
    gitcoin_data.event_type,
    gitcoin_data.event_source_id,
    gitcoin_data.event_source,
    gitcoin_data.to_project_name,
    gitcoin_data.from_project_name,
    gitcoin_data.amount
  from gitcoin_data
)

select
  grants.time,
  grants.event_type,
  grants.event_source_id,
  grants.event_source,
  grants.to_project_name,
  to_projects.project_id as to_project_id,
  'WALLET' as to_type,
  grants.from_project_name,
  from_projects.project_id as from_project_id,
  'WALLET' as from_type,
  grants.amount
from grants
inner join {{ ref('projects_v1') }} as to_projects
  on grants.to_project_name = to_projects.project_name
inner join {{ ref('projects_v1') }} as from_projects
  on grants.from_project_name = from_projects.project_name
