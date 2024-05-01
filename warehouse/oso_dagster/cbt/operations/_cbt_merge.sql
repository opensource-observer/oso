MERGE {{ source(destination_table).fqdn }} AS destination
USING (
  {{ select_query }}
) AS source
ON destination.{{ unique_column }} = source.{{ unique_column }}
WHEN MATCHED THEN
    UPDATE SET {{ source(destination_table).update_columns_with("destination", "source", exclude=[unique_column]) }}
WHEN NOT MATCHED THEN 
    INSERT ({{ source(destination_table).select_columns() }}) VALUES ({{ source(destination_table).select_columns(prefix="source") }})