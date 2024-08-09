{% macro potential_bots(network_name) %}
{% set lower_network_name = network_name.lower() %}
{% set upper_network_name = network_name.upper() %}

with sender_transfer_rates as (
    select 
        '{{ lower_network_name }}' as chain_name
        ,date_trunc(block_timestamp, hour) as hr
        ,from_address as sender
        ,min(block_timestamp) as min_block_time
        ,max(block_timestamp) as max_block_time
        ,count(*) as hr_txs
    from {{ oso_source(lower_network_name, "transactions") }}
    where 
        gas_price > 0 
        and receipt_gas_used > 0
    group by 1, 2, 3
)

,first_pass_throughput_filter as (
  select 
    chain_name,
    sender,
    date_trunc(hr, week) as wk,
    sum(hr_txs) as wk_txs,
    max(hr_txs) as max_hr_txs,
    cast(count(*) as float64) / cast(7.0 * 24.0 as float64) as pct_weekly_hours_active,
    min(min_block_time) as min_block_time,
    max(max_block_time) as max_block_time
  from sender_transfer_rates
  group by 1, 2, 3
  having
    max(hr_txs) >= 20
    or cast(count(*) as float64) / cast(7.0 * 24.0 as float64) >= 0.5
)
,aggregated_data as (
  select 
    chain_name,
    sender as address,
    max(wk_txs) as max_wk_txs,
    max(max_hr_txs) as max_hr_txs,
    avg(wk_txs) as avg_wk_txs,
    min(min_block_time) as min_block_time,
    max(max_block_time) as max_block_time,
    max(pct_weekly_hours_active) as max_pct_weekly_hours_active,
    avg(pct_weekly_hours_active) as avg_pct_weekly_hours_active,
    sum(wk_txs) as num_txs
  from first_pass_throughput_filter 
  group by 1, 2
)
select 
  *,
  (cast(timestamp_diff(max_block_time, min_block_time, second) as float64) / (60.0 * 60.0)) as txs_per_hour
from aggregated_data
where
  ( max_wk_txs >= 2000 and max_hr_txs >= 100 )
  or ( max_wk_txs >= 4000 and max_hr_txs >= 50 )
  or avg_wk_txs >= 1000 
  or (
    (cast(timestamp_diff(max_block_time, min_block_time, second) as float64) / (60.0 * 60.0)) >= 25
    and num_txs >= 100
  )
  or avg_pct_weekly_hours_active > 0.5
  or max_pct_weekly_hours_active > 0.95

{% endmacro %}
