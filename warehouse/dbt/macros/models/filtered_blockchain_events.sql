{% macro filtered_blockchain_events(artifact_source, source_name, source_table) %}
with known_addresses as (
  select distinct `artifact_source_id` as `address`
  from {{ ref("int_artifacts_by_project") }} 
  where `artifact_source` = '{{ artifact_source }}'
), known_to as (
select events.* 
from {{ oso_source(source_name, source_table)}} as events
inner join known_addresses known
  on known.address = events.to_address
  {% if is_incremental() %}
    {# 
      We are using insert_overwrite so this will consistently select everything
      that would go into the latest partition (and any new partitions after
      that). It will overwrite any data in the partitions for which this select
      statement matches
    #}
  where block_timestamp > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
    {{ playground_filter("block_timestamp", is_start=False) }}
  {% else %}
  {{ playground_filter("block_timestamp") }}
  {% endif %}
), known_from as (
  select events.* 
  from {{ oso_source(source_name, source_table)}} as events
  inner join known_addresses known
    on known.address = events.from_address
  {% if is_incremental() %}
  where block_timestamp > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
    {{ playground_filter("block_timestamp", is_start=False) }}
  {% else %}
  {{ playground_filter("block_timestamp") }}
  {% endif %}
), txs_with_dupes as (
  select * from known_to
  union all
  select * from known_from
)
select
  *
from txs_with_dupes
qualify
  ROW_NUMBER() OVER (PARTITION BY `id` ORDER BY block_timestamp ASC) = 1
{% endmacro %}