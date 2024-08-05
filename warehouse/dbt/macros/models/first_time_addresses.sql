{% macro first_time_addresses(network_name, block_timestamp_column="block_timestamp") %}

{% set lower_network_name = network_name.lower() %}

-- todo:
-- 1. add first funded by
-- 2. most funded by
select 
    address
    ,chain_name
    ,first_block_timestamp
    ,date_trunc(first_block_timestamp, day) as first_active_day
    ,format_timestamp('%Y-%m', date_trunc(first_block_timestamp, month)) as month_cohort
    ,first_block_number
    ,first_tx_to
    ,first_tx_hash
    ,first_method_id
from (
    select 
        from_address as address
        ,'{{ lower_network_name }}' as chain_name
        ,min(block_timestamp) as first_block_timestamp
        ,min(block_number) as first_block_number
        ,min_by(to_address, block_number) as first_tx_to
        ,min_by(`hash`, block_number) as first_tx_hash
        ,min_by(substring(input, 1, 10), block_number) as first_method_id
    from {{ ref('int_%s_transactions' % lower_network_name) }}
    where 
      gas_price > 0
      and receipt_status = 1
      and receipt_gas_used > 0
    {% if is_incremental() %}
      and {{ block_timestamp_column }} > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
    {% else %}
      {{ playground_filter(block_timestamp_column, is_start=False) }}
    {% endif %}
    group by 1, 2
)
{% endmacro %}
