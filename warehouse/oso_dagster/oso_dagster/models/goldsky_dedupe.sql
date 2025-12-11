SELECT 
  {% if partition_column_name %}
    {{ source(raw_table).select_columns(exclude=[partition_column_name]) }},
    {{ partition_column_transform(partition_column_name) }} AS `{{ partition_column_name }}`
  {% else %}
    {{ source(raw_table).select_columns() }}
  {% endif %}
FROM {{ source(raw_table).fqdn }} AS worker
QUALIFY ROW_NUMBER() OVER (PARTITION BY `{{ unique_column }}` ORDER BY `{{ order_column }}` DESC) = 1