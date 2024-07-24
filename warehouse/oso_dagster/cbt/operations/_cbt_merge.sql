MERGE {{ source(destination_table).fqdn }} AS destination
USING (
  {{ select_query }}
) AS source
ON destination.{{ unique_column }} = source.{{ unique_column }} 
  {% if time_partitioning -%} 
  AND destination.{{ time_partitioning.column }} >= TIMESTAMP_TRUNC(TIMESTAMP_SUB(TIMESTAMP('{{ time_range.start.format("YYYY-MM-DD") }}'), INTERVAL 1 DAY), {{ time_partitioning.type}})
  {%- endif %}
{% set update_str = source(destination_table).update_columns_with("destination", "source", exclude=[unique_column]) %}
{% if update_str != "" %}
WHEN MATCHED THEN
  UPDATE SET {{ update_str }}
{% endif %}
WHEN NOT MATCHED THEN 
    INSERT ({{ source(destination_table).select_columns() }}) 
    VALUES ({{ source(destination_table).select_columns(prefix="source") }})