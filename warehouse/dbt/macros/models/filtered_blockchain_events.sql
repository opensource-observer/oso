{% macro filtered_blockchain_events(artifact_source, source_name, source_table) %}
with known_addresses as (
  select distinct `artifact_source_id` as `address`
  from {{ ref("int_artifacts_by_project") }} 
  where `artifact_source` = '{{ artifact_source }}'
)
select * 
from {{ oso_source(source_name, source_table)}}
where 
  to_address in (select * from known_addresses) 
  or from_address in (select * from known_addresses)
  {% if is_incremental() %}
    {# 
      We are using insert_overwrite so this will consistently select everything
      that would go into the latest partition (and any new partitions after
      that). It will overwrite any data in the partitions for which this select
      statement matches
    #}
    and block_timestamp > TIMESTAMP_SUB(_dbt_max_partition, INTERVAL 1 DAY)
  {% endif %}
{% endmacro %}