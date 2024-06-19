SELECT 
  count(blocks.{{ blocks_block_hash_column_name }}) as missing_block_hashes,
  sum(blocks.{{ blocks_transaction_count_column_name }}) as missing_transactions
FROM blocks as blocks
LEFT JOIN transactions txs
  ON txs.{{ transactions_block_hash_column_name }} = blocks.{{ blocks_block_hash_column_name }}
WHERE txs.{{ transactions_block_hash_column_name }} is null and blocks.{{ blocks_transaction_count_column_name }} != 0