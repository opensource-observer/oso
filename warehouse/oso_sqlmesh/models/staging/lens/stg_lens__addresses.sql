MODEL (
    name oso.stg_lens__addresses,
    description 'Get lens addresses info',
    dialect trino,
    kind FULL,
    audits (
        has_at_least_n_rows(threshold := 0)
    )
);

WITH addresses_ordered AS (
    SELECT
        @oso_entity_id('LENS', '', address) AS network_address,
        addresses.address AS lens_address,
        addresses.bytecode AS address_bytecode,
        addresses.createdAt AS address_creation,
        addresses.updatedAt AS address_update,
        addresses.creatorTxHash AS creator_tx,
        addresses.creatorAddress AS creator,
        addresses.createdInLogIndex AS creation_log_index,
        addresses.isEvmLike AS is_evm_like,
        ROW_NUMBER() OVER (
            PARTITION BY addresses.address
            ORDER BY addresses.updatedAt DESC
        ) AS row_number
    FROM @oso_source('bigquery.lens_chain_mainnet.addresses') AS addresses
)
SELECT
    network_address,
    lens_address,
    address_bytecode,
    address_creation,
    address_update,
    creator_tx,
    creator,
    creation_log_index,
    is_evm_like
FROM addresses_ordered
WHERE row_number = 1
