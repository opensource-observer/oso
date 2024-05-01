WITH optimism_blocks AS (
  SELECT block_timestamp, block_number
  FROM `bigquery-public-data.goog_blockchain_optimism_mainnet_us.blocks`
)
SELECT blocks.block_timestamp, {{ source(worker_table).select_columns(prefix="traces", exclude=["_checkpoint", "block_timestamp"]) }}
FROM {{ source(worker_table).fqdn }} AS traces
INNER JOIN `bigquery-public-data.goog_blockchain_optimism_mainnet_us.blocks` AS blocks
  ON blocks.block_number = traces.block_number
QUALIFY ROW_NUMBER() OVER (PARTITION BY `{{ unique_column }}` ORDER BY `{{ order_column }}` DESC) = 1