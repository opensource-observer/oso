{% set networks = ["optimism", "base", "frax", "metal", "mode", "zora"] %}
{% set start_date = '2023-10-01' %}
{% set end_date = '2024-06-01' %}
{% set union_queries = [] %}

{% for network in networks %}
  {% set table_name = "stg_" ~ network ~ "__proxies" %}
  {% set network_upper = network.upper() %}

  {% set query %}
  select  
    '{{ network_upper }}' as network,
    block_timestamp,
    transaction_hash,
    case
      when proxy_address = from_address then to_address
      else from_address
    end as address,
    case
      when proxy_address = from_address then 'to'
      else 'from'
    end as transaction_type
  from {{ ref(table_name) }}
  where
    proxy_type = 'ENTRYPOINT'
    and block_timestamp > '{{ start_date }}'
    and block_timestamp < '{{ end_date }}'
  {% endset %}

  {% do union_queries.append(query) %}
{% endfor %}

{% set final_query = union_queries | join(' union all ') %}

with txns as (
  {{ final_query }}
),

tagged_txns as (
  select
    txns.*,
    artifacts_by_project_v1.project_id,
    artifacts_by_project_v1.project_name
  from txns
  left join {{ ref('artifacts_by_project_v1') }}
    on
      txns.address = artifacts_by_project_v1.artifact_name
      and txns.network = artifacts_by_project_v1.artifact_source
),

relevant_txns as (
  select tagged_txns.*
  from tagged_txns
  where transaction_hash in (
    select distinct transaction_hash
    from tagged_txns
    where
      project_id is not null
      and transaction_type = 'to'
      and address not in (
        lower('0x0000000071727De22E5E9d8BAf0edAc6f37da032'),
        lower('0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789')
      )
  )
),

raw_4337_events as (
  select
    relevant_txns.project_id,
    relevant_txns.project_name,
    relevant_txns.transaction_hash,
    relevant_txns.network as event_source,
    relevant_txns.address as to_artifact_name,
    txns.address as from_artifact_name,
    timestamp_trunc(relevant_txns.block_timestamp, day) as bucket_day
  from relevant_txns
  left join txns
    on relevant_txns.transaction_hash = txns.transaction_hash
  where
    txns.transaction_type = 'from'
)

select
  bucket_day,
  project_id,
  project_name,
  from_artifact_name,
  to_artifact_name,
  event_source,
  '4337_INTERACTION' as event_type,
  count(distinct transaction_hash) as amount
from raw_4337_events
where project_id is not null
group by
  bucket_day,
  project_id,
  project_name,
  from_artifact_name,
  to_artifact_name,
  event_source
