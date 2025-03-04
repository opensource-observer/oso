model(name oso.int_contracts_overview, kind full,)
;

select
    derived_contracts.deployment_timestamp as deployment_timestamp,
    derived_contracts.contract_address,
    derived_contracts.chain as contract_namespace,
    derived_contracts.originating_address as originating_address,
    derived_contracts.factory_address,
    derived_contracts.root_deployer_address as root_deployer_address,
    sort_weights.sort_weight as sort_weight
from oso.int_derived_contracts as derived_contracts
inner join
    oso.int_derived_contracts_sort_weights as sort_weights
    on derived_contracts.contract_address = sort_weights.contract_address
    and derived_contracts.chain = sort_weights.chain
