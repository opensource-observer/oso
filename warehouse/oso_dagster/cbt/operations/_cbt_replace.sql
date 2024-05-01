CREATE OR REPLACE TABLE {{ source(destination_table).fqdn }}
{% if time_partitioning %}
  PARTITION BY TIMESTAMP_TRUNC({{ time_partitioning.column }}, {{ time_partitioning.type }})
{% endif %}
AS 
{{ select_query }}