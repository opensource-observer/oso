{{
  config(
    materialized='table'
  )
}}

{% set networks = ["optimism", "base", "frax", "metal", "mode", "zora"] %}

{% set union_factory_queries = [] %}
{% set union_deployer_queries = [] %}

{% for network in networks %}

  {% set network_upper = network.upper() %}

  {% set factory_table = "stg_" ~ network ~ "__factories" %}
  {% set query %}
  select
    factory_address,
    contract_address,
    '{{ network_upper }}' as network
  from {{ ref(factory_table) }}
  {% endset %}
  {% do union_factory_queries.append(query) %}

  {% set deployer_table = "stg_" ~ network ~ "__deployers" %}
  {% set query %}
  select
    deployer_address,
    contract_address,
    '{{ network_upper }}' as network
  from {{ ref(deployer_table) }}
  {% endset %}
  {% do union_deployer_queries.append(query) %}

{% endfor %}

{% set all_factories = union_factory_queries | join(' union all ') %}
{% set all_deployers = union_deployer_queries | join(' union all ') %}

with factories as (
  {{ all_factories }}
),

deployers as (
  {{ all_deployers }}
),

oso_addresses as (
  select distinct
    apps.application_id,
    artifacts_by_project.artifact_source as network,
    artifacts_by_project.artifact_name as contract_address
  from {{ source('static_data_sources', 'agora_rf4_applications') }} as apps
  left join {{ ref('artifacts_by_project_v1') }} as artifacts_by_project
    on apps.oso_project_name = artifacts_by_project.project_name
  where
    artifacts_by_project.artifact_source in (
      'OPTIMISM', 'BASE', 'FRAX', 'METAL', 'MODE', 'ZORA'
    )
),

oso_contracts as (
  select
    oso_addresses.application_id,
    oso_addresses.network,
    oso_addresses.contract_address
  from oso_addresses
  left join deployers
    on
      oso_addresses.contract_address = deployers.contract_address
      and oso_addresses.network = deployers.network
  where deployers.contract_address is not null
),

agora_contracts as (
  select
    application_id,
    artifact_source as network,
    artifact as contract_address
  from {{ source('static_data_sources', 'agora_rf4_artifacts_by_app') }}
  where artifact_type = 'CONTRACT'
),

app_contracts as (
  select
    application_id,
    network,
    contract_address,
    'oso' as source
  from oso_contracts
  union all
  select
    application_id,
    network,
    contract_address,
    'agora' as source
  from agora_contracts
),

discovered_contracts as (
  select
    app_contracts.application_id,
    factories.contract_address,
    factories.network,
    'discovered' as source
  from factories
  left join app_contracts
    on
      factories.factory_address = app_contracts.contract_address
      and factories.network = app_contracts.network
  where app_contracts.application_id is not null
),

contracts as (
  select
    application_id,
    contract_address,
    network,
    source
  from discovered_contracts
  union all
  select
    application_id,
    contract_address,
    network,
    source
  from app_contracts
)

select distinct
  application_id,
  contract_address,
  network,
  source
from contracts
where application_id is not null
