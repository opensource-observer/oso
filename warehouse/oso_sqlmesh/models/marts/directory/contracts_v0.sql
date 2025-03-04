model(name oso.contracts_v0, kind view, tags('export'),)
;

select
    date_trunc('day', deployment_timestamp)::date as deployment_date,
    contract_address,
    contract_namespace,
    originating_address,
    factory_address,
    root_deployer_address,
    sort_weight
from oso.int_contracts_overview
