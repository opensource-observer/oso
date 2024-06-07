{% macro known_proxies(network_name, start, traces="traces") %}

{# 
  Important information
  
  CHAIN IDs:
    * Optimism: 10
    * Frax: 252
    * Base: 8453
    * Metal: 1750
    * Mode: 34443
    * PGN: 424
    * Zora: 7777777

  This is the 4337 contract address for Safe4337Module
  - 0xa581c4A4DB7175302464fF3C06380BC3270b4037
  https://docs.safe.global/home/4337-supported-networks
#}

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
    proxies.proxy_type,
    traces.from_address as proxy_address,
    traces.to_address
  from {{ source(network_name, traces) }} as traces
  inner join proxy_contracts as proxies
    on lower(traces.from_address) = lower(proxies.factory_address)
  where
    traces.block_timestamp >= {{ start }}
    and traces.trace_type = 'call'
    and traces.from_address != traces.to_address
)
select
  id,
  block_timestamp,
  transaction_hash,
  proxy_type,
  proxy_address,
  to_address
from proxy_txns

{% endmacro %}