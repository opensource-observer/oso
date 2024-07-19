MERGE {{ source(destination_table).fqdn }} AS destination
USING (
  {{ select_query }}
) AS source
ON destination.{{ unique_column }} = source.{{ unique_column }} 
  AND destination.{{ time_partitioning.column }} >= TIMESTAMP_TRUNC(TIMESTAMP_SUB(TIMESTAMP('{{ time_range.start.format("YYYY-MM-DD") }}'), INTERVAL 1 DAY), {{ time_partitioning.type}})
WHEN MATCHED THEN
    UPDATE SET {{ source(destination_table).update_columns_with("destination", "source", exclude=[unique_column]) }}
WHEN NOT MATCHED THEN 
    INSERT ({{ source(destination_table).select_columns() }}) 
    VALUES ({{ source(destination_table).select_columns(prefix="source") }})
-- Delete anything that doesn't appear in the source. This effectively replaces
-- any data in partitions that are being scanned with this merge
WHEN NOT MATCHED BY SOURCE 
    DELETE