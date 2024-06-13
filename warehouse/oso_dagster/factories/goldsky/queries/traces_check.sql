SELECT 
  count(distinct txs.{{ transactions_transaction_hash_column_name }}) as missing_transaction_hashes
FROM transactions txs
LEFT JOIN traces traces
  ON txs.{{ transactions_transaction_hash_column_name }} = traces.{{ traces_transaction_hash_column_name }}
WHERE traces.{{ traces_transaction_hash_column_name }} is null