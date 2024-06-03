{% macro known_proxies(network_name, start, traces_source_name, traces_source_table) %}
{% set lower_network_name = network_name.lower() %}
{% set upper_network_name = network_name.upper() %}

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

  This is the deployer for the deterministic deployer
  - 0x3fab184622dc19b6109349b94811493bf2a45362

  This is the 4337 contract address for safes
  - 0xa581c4A4DB7175302464fF3C06380BC3270b4037

  For optimism this is the EntryPoint (I think) for ERC-4337
  - 0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789
#}

with proxy_contracts as (
  SELECT * FROM UNNEST([
    STRUCT('SAFE' as proxy_type, '1.3.0' as `version`, lower('0xC22834581EbC8527d974F8a1c97E1bEA4EF910BC') as factory_address),
    ('SAFE', '1.4.0', lower('0x4e1DCf7AD4e460CfD30791CCC4F9c8a4f820ec67'))
  ])
), safes as (
  select 
    traces.block_timestamp, 
    traces.transaction_hash, 
    proxies.proxy_type as proxy_type,
    traces.to_address 
  from {{ oso_source(traces_source_name, traces_source_table) }} as traces
  inner join proxy_contracts as proxies
    on lower(traces.from_address) = lower(proxies.factory_address)
  where
    block_timestamp >= {{ start }}
    {# some duplicates were discovered in the dataset that had id's starting with `geth_` #}
    and id not like 'geth_%'
    and trace_type = 'create2'
)
select * from safes
{% endmacro %}
