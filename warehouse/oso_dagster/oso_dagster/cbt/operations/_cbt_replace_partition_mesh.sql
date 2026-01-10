MERGE @VAR('destination') AS destination
USING @VAR('source') AS source
ON destination.unique_column = source.unique_column
  AND TIMESTAMP_TRUNC(destination.@VAR('time_column'), DAY) = TIMESTAMP_TRUNC(source.@VAR('time_column'), DAY)
WHEN MATCHED THEN
    UPDATE SET @STAR_SET(@VAR('source'), @VAR('destination'), exclude := ['unique_column', @VAR('time_column')])
WHEN NOT MATCHED THEN 
    INSERT (@STAR_NO_CAST(@VAR('source'))) 
    VALUES ({{ source(destination_table).select_columns(prefix="source") }})
-- Delete anything that doesn't appear in the source. This effectively replaces
-- any data in partitions that are being scanned with this merge
WHEN NOT MATCHED BY SOURCE 
    DELETE