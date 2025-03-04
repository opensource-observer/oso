model(name oso.int_factories, kind view)
;

select
    block_timestamp,
    transaction_hash,
    originating_address,
    originating_contract,
    factory_address,
    contract_address,
    create_type,
    upper(chain) as chain
from oso.stg_superchain__factories
