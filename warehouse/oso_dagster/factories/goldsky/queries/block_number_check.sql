SELECT 
  MIN({{ block_number_column_name }}) as min_block_number, 
  MAX({{ block_number_column_name }}) as max_block_number, 
  COUNT(DISTINCT {{ block_number_column_name }}) as blocks_count 
FROM blocks