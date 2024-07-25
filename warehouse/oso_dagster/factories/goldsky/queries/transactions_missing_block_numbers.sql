-- This finds any missing block numbers for the transactions table by using the
-- block number from the blocks that are missing transactions. Correctness
-- relies on the blocks data being whole. Things need to be recalculated
-- otherwise.

SELECT DISTINCT
  blocks.{{ blocks_block_number_column_name }} as `block_number`
FROM blocks as blocks
LEFT JOIN transactions txs
  ON txs.{{ transactions_block_hash_column_name }} = blocks.{{ blocks_block_hash_column_name }}
WHERE 
  txs.{{ transactions_block_hash_column_name }} is null 
  and blocks.{{ blocks_transaction_count_column_name }} > 0