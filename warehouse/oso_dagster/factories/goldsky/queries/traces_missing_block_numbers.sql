-- This finds any missing block numbers for traces table by using the block
-- number from the transactions that are missing traces. This assumes that
-- blocks aren't missing but if that's the case then more problems likely exist.

SELECT DISTINCT
  txs.{{ transactions_block_number_column_name }} as block_number,
FROM transactions txs
LEFT JOIN traces traces
  ON txs.{{ transactions_transaction_hash_column_name }} = traces.{{ traces_transaction_hash_column_name }}
WHERE traces.{{ traces_transaction_hash_column_name }} is null