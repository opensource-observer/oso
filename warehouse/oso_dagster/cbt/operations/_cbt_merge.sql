{# 
  source_table_fqn is optional and allows for the 
  destination to compare columns to the source to ensure compatibility 
#}
{% if not source_table_fqn %}
{% set source_table = None %}
{% else %}
{% set source_table = source(source_table_fqn) %}
{% endif %}

MERGE {{ source(destination_table).fqdn }} AS destination
USING (
  {{ select_query }}
) AS source
ON destination.{{ unique_column }} = source.{{ unique_column }} 
  {% if time_partitioning -%} 
  AND destination.{{ time_partitioning.column }} >= TIMESTAMP_TRUNC(TIMESTAMP_SUB(TIMESTAMP('{{ time_range.start.format("YYYY-MM-DD") }}'), INTERVAL 1 DAY), {{ time_partitioning.type}})
  {%- endif %}
{% set update_str = source(destination_table).update_columns_with("destination", "source", source_table=source_table, exclude=[unique_column], fail_with_additional_columns=True) %}
{% if update_str != "" %}
WHEN MATCHED THEN
  UPDATE SET {{ update_str }}
{% endif %}
WHEN NOT MATCHED THEN 
    INSERT ({{ source(destination_table).select_columns(intersect_columns_with=source_table) }}) 
    VALUES ({{ source(destination_table).select_columns(intersect_columns_with=source_table, prefix="source") }})