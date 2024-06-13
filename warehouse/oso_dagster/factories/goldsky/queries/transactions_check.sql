SELECT 
  count(distinct blocks.{{ blocks_block_hash_column_name }}) as missing_block_hashes
FROM blocks as blocks
LEFT JOIN transactions txs
  ON txs.{{ transactions_block_hash_column_name }} = blocks.{{ blocks_block_hash_column_name }}
WHERE txs.{{ transactions_block_hash_column_name }} is null