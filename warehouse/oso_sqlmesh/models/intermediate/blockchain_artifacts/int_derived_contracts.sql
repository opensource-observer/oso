model(name oso.int_derived_contracts, kind view)
;

select
    deployment_timestamp::timestamp(6),
    chain::varchar,
    originating_address::varchar,
    contract_address::varchar,
    factory_address::varchar,
    create_type::varchar,
    root_deployer_address::varchar,
from oso.int_contracts_root_deployers
