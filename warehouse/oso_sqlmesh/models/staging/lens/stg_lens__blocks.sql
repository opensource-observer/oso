MODEL (
    name oso.stg_lens__blocks,
    description 'Info on each block on the lens blockchain',
    dialect trino,
    kind FULL,
    audits (
        has_at_least_n_rows(threshold := 0)
    )
);

WITH blocks_ordered AS (
    SELECT
        blocks.number AS block_number,
        blocks.nonce as block_nonce,
        blocks.difficulty AS difficulty,
        blocks.gasLimit AS gas_limit,
        blocks.gasUsed AS gas_used,
        blocks.baseFeePerGas AS base_fee_per_gas,
        blocks.l1BatchNumber AS l1_batch_number,
        blocks.l1TxCount AS l1_tx_count,
        blocks.l2TxCount AS l2_tx_count,
        blocks.hash AS block_hash,
        blocks.parentHash AS parent_hash,
        blocks.miner AS miner,
        blocks.extraData AS extra_data,
        blocks.timestamp AS block_timestamp,
        blocks.createdAt AS block_creation,
        blocks.updatedAt AS block_update,
        ROW_NUMBER() OVER (
            PARTITION BY blocks.number
            ORDER BY blocks.updatedAt DESC
        ) AS row_number
    FROM @oso_source('bigquery.lens_chain_mainnet.blocks') AS blocks
)

SELECT
    block_number,
    block_nonce,
    difficulty,
    gas_limit,
    gas_used,
    base_fee_per_gas,
    l1_batch_number,
    l1_tx_count,
    l2_tx_count,
    block_hash,
    parent_hash,
    miner,
    extra_data,
    block_timestamp,
    block_creation,
    block_update
FROM blocks_ordered
WHERE row_number = 1