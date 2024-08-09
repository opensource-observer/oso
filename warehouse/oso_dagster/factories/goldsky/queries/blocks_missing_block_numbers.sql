-- This finds any missing block numbers for a blocks tables on a given range.
-- It's best to use this in a sliding fashion over the course of a few days.

with continous_block_number_series (
  SELECT `block_number`
  FROM (
    SELECT
      MIN({{ block_number_column_name }}) as min_block_number,
      MAX({{ block_number_column_name }}) as max_block_number
    FROM blocks
  ) as blocks_range
  CROSS JOIN UNNEST(GENERATE_ARRAY(blocks_range.min_block_number, blocks_range.max_block_number)) as `block_number`
)
SELECT 
  series.block_number,
FROM continous_block_number_series as series
LEFT JOIN blocks
  ON series.block_number = blocks.{{ block_number_column_name }}
WHERE blocks.{{ block_number_column_name}} is null