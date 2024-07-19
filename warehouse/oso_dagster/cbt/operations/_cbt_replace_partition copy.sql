MERGE destination AS destination
USING source AS source
ON destination.unique_column = source.unique_column
  AND destination.time_partitioning_column >= TIMESTAMP_TRUNC(TIMESTAMP_SUB(timestamp_ts, INTERVAL 1 DAY), timestamp_type)
WHEN MATCHED THEN
    UPDATE SET {{ source(destination_table).update_columns_with("destination", "source", exclude=[unique_column]) }}
WHEN NOT MATCHED THEN 
    INSERT ({{ source(destination_table).select_columns() }}) 
    VALUES ({{ source(destination_table).select_columns(prefix="source") }})
-- Delete anything that doesn't appear in the source. This effectively replaces
-- any data in partitions that are being scanned with this merge
WHEN NOT MATCHED BY SOURCE 
    DELETE