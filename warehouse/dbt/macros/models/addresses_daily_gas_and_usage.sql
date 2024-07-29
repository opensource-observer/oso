{% macro addresses_daily_gas_and_usage(network_name) %}
{% set lower_network_name = network_name.lower() %}

with daily_gas_fees as (
    select 
        address
        ,date_trunc(block_timestamp, day) as date_timestamp
        ,sum( (gas_price * receipt_gas_used) / 1e18) as l2_gas_paid
        ,sum(receipt_l1_fee / 1e18) as l1_gas_paid
        ,sum(receipt_l1_fee / 1e18 + (gas_price * receipt_gas_used) / 1e18) as total_gas_fees_paid
        ,count(hash) as num_txs
        ,1 as num_days_active
    from {{ oso_source(lower_network_name, "transactions") }}
    where
        true
        and receipt_status = 1
        and gas_price > 0 
        and receipt_gas_used > 0
        {% if is_incremental() %}
        and block_timestamp > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
        {% else %}
        {{ playground_filter(block_timestamp, is_start=False) }}
        {% endif %}
    group by 1, 2, 7
)

,max_timestamp as (
    select 
        max(date_timestamp) as max_date
    from daily_gas_fees
)

-- generating daily record for each address that has ever been active
,addition as (
    select 
        ft.address
        ,ft.chain_name
        ,ft.month_cohort
        ,c.date_timestamp
        ,date_diff(c.date_timestamp, ft.first_active_day, DAY) as days_since_first_active
    from {{ ref('stg_%s__first_time_addresses' % lower_network_name)}} as ft 
    join {{ ref('stg_utility__calendar')}} as c 
        on c.date_timestamp >= ft.first_active_day
        and c.date_timestamp < (select max_date from max_timestamp)
    where
        true
        {% if is_incremental() %}
            and c.date_timestamp > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
        {% else %}
            {{ playground_filter(c.date_timestamp, is_start=False) }}
        {% endif %}
)

select 
    a.*
    ,coalesce(d.l2_gas_paid, 0) as l2_gas_paid
    ,coalesce(d.l1_gas_paid, 0) as l1_gas_paid
    ,coalesce(d.total_gas_fees_paid, 0) as total_gas_fees_paid
    ,coalesce(d.num_txs, 0) as num_txs
    ,coalesce(d.num_days_active, 0) as num_days_active
from addition as a 
left join daily_gas_fees as d 
    on a.address = d.address
    and a.date_timestamp = d.date_timestamp

{% endmacro %}
