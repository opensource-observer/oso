SELECT 
  blocks.{{ blocks_block_hash_column_name }}) as block_hash
  blocks.{{ blocks_block_number_column_name }} as block_number,
  blocks.{{ blocks_block_timestamp_column_name }} as block_timestamp
FROM blocks as blocks
LEFT JOIN transactions txs
  ON txs.{{ transactions_block_hash_column_name }} = blocks.{{ blocks_block_hash_column_name }}
WHERE txs.{{ transactions_block_hash_column_name }} is null