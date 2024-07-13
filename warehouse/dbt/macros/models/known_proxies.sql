{% macro known_proxies(network_name, start, traces="traces") %}

{# 
  This model is used to help identify smart contract accounts by looking for transactions that interact with the most widespread proxy contracts.
#}

{% if target.name == 'playground' %}
{% set start = "TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL %s DAY)" % env_var('PLAYGROUND_DAYS', '90') %}
{% endif %}

with proxy_contracts as (
  select * 
    from UNNEST([ STRUCT
    (
      'SAFE' as proxy_type,
      '1.4.1' as `version`,
      LOWER('0x4e1DCf7AD4e460CfD30791CCC4F9c8a4f820ec67') as factory_address
    ),
    ( 
      'SAFE',
      '1.3.0',
      LOWER('0xC22834581EbC8527d974F8a1c97E1bEA4EF910BC')
    ), 
    (
      'SAFE',
      '1.1.1',
      LOWER('0x76E2cFc1F5Fa8F6a5b3fC4c8F4788F0116861F9B')
    ),
    (
      'SAFE',
      '1.0.0',
      LOWER('0x12302fE9c02ff50939BaAaaf415fc226C078613C')
    ),  
    (
      'ENTRYPOINT',
      '0.0.7',
      LOWER('0x0000000071727De22E5E9d8BAf0edAc6f37da032')
    ),
    (
      'ENTRYPOINT',
      '0.0.6',
      LOWER('0x5ff137d4b0fdcd49dca30c7cf57e578a026d2789')
    )
  ])
  
),
proxy_txns as (
  select 
    traces.id,
    traces.block_timestamp, 
    traces.transaction_hash,     
    traces.from_address,
    traces.to_address,
    proxies.proxy_type,
    case
      when lower(traces.from_address) = lower(proxies.factory_address)
      then traces.from_address
      when lower(traces.to_address) = lower(proxies.factory_address)
      then traces.to_address
      else null
    end as proxy_address
  from {{ oso_source(network_name, traces) }} as traces
  inner join proxy_contracts as proxies
    on lower(traces.from_address) = lower(proxies.factory_address)
    or lower(traces.to_address) = lower(proxies.factory_address)
  where
    traces.block_timestamp >= {{ start }}    
    and traces.status = 1
    and traces.trace_type = 'call'
    and traces.call_type != 'staticcall'
    and traces.from_address != traces.to_address
)
select
  id,
  block_timestamp,
  transaction_hash,
  proxy_type,
  proxy_address,
  from_address,
  to_address
from proxy_txns
where proxy_address is not null

{% endmacro %}