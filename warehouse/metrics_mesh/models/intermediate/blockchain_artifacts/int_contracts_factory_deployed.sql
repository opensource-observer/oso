MODEL (
  name metrics.int_contracts_factory_deployed,
  VIEW
);

select *
from metrics.int_contracts_first_deployment as contracts
where contracts.originating_address != contracts.factory_address