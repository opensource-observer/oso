{# 
  The most recent view of grants to projects from the oss-funding source.
#}

{% set oss_funding_url = "https://github.com/opensource-observer/oss-funding" %}

with oss_funding_data as (
  select -- noqa: ST06
    cast(funding_date as timestamp) as `time`,
    'GRANT_RECEIVED_USD' as event_type,
    '{{ oss_funding_url }}' as event_source_id,
    'OSS_FUNDING' as event_source,
    lower(to_project_name) as to_project_name,
    lower(from_funder_name) as from_project_name,
    coalesce(amount, 0) as amount,
    grant_pool_name,
    parse_json(metadata_json) as metadata_json
  from {{ source('static_data_sources', 'oss_funding_v1') }}
  where
    from_funder_name is not null
    and amount is not null
),

gitcoin_data as (
  select -- noqa: ST06
    event_time as `time`,
    'GRANT_RECEIVED_USD' as event_type,
    coalesce(
      transaction_hash,
      cast(gitcoin_project_id as string)
    ) as event_source_id,
    concat('GITCOIN', '_', upper(oso_generated_round_label)) as event_source,
    oso_project_name as to_project_name,
    'gitcoin' as from_project_name,
    amount_in_usd as amount,
    oso_generated_round_label as grant_pool_name,
    to_json(struct(
      gitcoin_data_source,
      gitcoin_round_id,
      round_number,
      round_type,
      main_round_label,
      round_name,
      chain_id,
      gitcoin_project_id,
      project_application_title,
      oso_project_id,
      oso_display_name,
      donor_address
    )) as metadata_json
  from {{ ref('int_gitcoin_funding_events') }}
),

open_collective_data as (
  select -- noqa: ST06
    ocd.`time`,
    'GRANT_RECEIVED_USD' as event_type,
    ocd.event_source_id,
    'OPEN_COLLECTIVE' as event_source,
    projects.project_name as to_project_name,
    'opencollective' as from_project_name,
    ocd.amount,
    'contributions' as grant_pool_name,
    to_json(struct(
      ocd.project_name as open_collective_project_name,
      ocd.project_slug as open_collective_project_slug,
      ocd.project_type as open_collective_project_type,
      ocd.currency as open_collective_currency,
      ocd.amount as open_collective_amount
    )) as metadata_json
  from {{ ref('int_open_collective_deposits') }} as ocd
  left join {{ ref('projects_v1') }} as projects
    on ocd.project_id = projects.project_id
  where ocd.currency = 'USD'
),

oso_indexed_data as (
  select
    gitcoin_data.time,
    gitcoin_data.event_type,
    gitcoin_data.event_source_id,
    gitcoin_data.event_source,
    gitcoin_data.to_project_name,
    gitcoin_data.from_project_name,
    gitcoin_data.amount,
    gitcoin_data.grant_pool_name,
    gitcoin_data.metadata_json
  from gitcoin_data
  union all
  select
    open_collective_data.time,
    open_collective_data.event_type,
    open_collective_data.event_source_id,
    open_collective_data.event_source,
    open_collective_data.to_project_name,
    open_collective_data.from_project_name,
    open_collective_data.amount,
    open_collective_data.grant_pool_name,
    open_collective_data.metadata_json
  from open_collective_data
),

grants as (
  select
    oss_funding_data.time,
    oss_funding_data.event_type,
    oss_funding_data.event_source_id,
    oss_funding_data.event_source,
    oss_funding_data.to_project_name,
    oss_funding_data.from_project_name,
    oss_funding_data.amount,
    oss_funding_data.grant_pool_name,
    oss_funding_data.metadata_json
  from oss_funding_data

  union all

  select
    oso_indexed_data.time,
    oso_indexed_data.event_type,
    oso_indexed_data.event_source_id,
    oso_indexed_data.event_source,
    oso_indexed_data.to_project_name,
    oso_indexed_data.from_project_name,
    oso_indexed_data.amount,
    oso_indexed_data.grant_pool_name,
    oso_indexed_data.metadata_json
  from oso_indexed_data
)

select
  grants.time,
  grants.event_type,
  grants.event_source_id,
  grants.event_source,
  grants.to_project_name,
  to_projects.project_id as to_project_id,
  'FISCAL_HOST' as to_type,
  grants.from_project_name,
  from_projects.project_id as from_project_id,
  'WALLET' as from_type,
  grants.amount,
  grants.grant_pool_name,
  grants.metadata_json
from grants
left join {{ ref('projects_v1') }} as to_projects
  on grants.to_project_name = to_projects.project_name
inner join {{ ref('projects_v1') }} as from_projects
  on grants.from_project_name = from_projects.project_name
