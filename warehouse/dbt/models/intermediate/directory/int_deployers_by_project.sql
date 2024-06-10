{{
  config(
    materialized='table'
  )
}}

{# TODO: Add Ethereum / Mainnet and Arbitrum (One) to list of networks #}

{% set networks = ["optimism", "base", "frax", "metal", "mode", "zora"] %}

{% set union_queries = [] %}

{% for network in networks %}
  {% set table_name = "stg_" ~ network ~ "__deployers" %}
  {% set network_upper = network.upper() %}

  {% set query %}
  select distinct
    deployer_address,
    '{{ network_upper }}' as network
  from {{ ref(table_name) }}
  {% endset %}

  {% do union_queries.append(query) %}
{% endfor %}

{% set final_query = union_queries | join(' union all ') %}

with all_deployers as (
  {{ final_query }}
),

known_deployers as (
  select distinct
    project_id,
    artifact_source,
    artifact_name
  from {{ ref('int_artifacts_in_ossd_by_project') }}
  where artifact_type = 'DEPLOYER'
),

any_evm_deployers as (
  select
    known_deployers.project_id,
    all_deployers.deployer_address,
    all_deployers.network
  from all_deployers
  left join known_deployers
    on all_deployers.deployer_address = known_deployers.artifact_name
  where
    known_deployers.project_id is not null
    and known_deployers.artifact_source = 'ANY_EVM'
),

chain_specific_deployers as (
  select
    known_deployers.project_id,
    all_deployers.deployer_address,
    all_deployers.network
  from all_deployers
  left join known_deployers
    on
      all_deployers.deployer_address = known_deployers.artifact_name
      and all_deployers.network = known_deployers.artifact_source
  where
    known_deployers.project_id is not null
    and known_deployers.artifact_source != 'ANY_EVM'
),

verified_deployers as (
  select
    project_id,
    deployer_address,
    network
  from any_evm_deployers
  union all
  select
    project_id,
    deployer_address,
    network
  from chain_specific_deployers
),

deployers as (
  select distinct
    project_id,
    deployer_address as artifact_name,
    network as artifact_source
  from verified_deployers
)

select
  project_id,
  {{ oso_id("artifact_source", "artifact_name") }} as artifact_id,
  artifact_source,
  artifact_name as artifact_source_id,
  LOWER(artifact_source) as artifact_namespace,
  artifact_name
from deployers
