model(
    name oso.int_deployers,
    kind incremental_by_time_range(
        time_column block_timestamp, batch_size 365, batch_concurrency 1
    ),
    start '2021-10-01',
    partitioned_by(day("block_timestamp"), "chain"),
)
;

select
    block_timestamp,
    transaction_hash,
    deployer_address,
    contract_address,
    upper(chain) as chain
from oso.stg_superchain__deployers
