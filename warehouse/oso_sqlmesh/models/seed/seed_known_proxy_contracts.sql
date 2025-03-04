-- Purpose: Seed data for known proxy contracts. To update this data, please
-- update the CSV file at the path specified below. This can be used for any evm
-- chain.
model(
    name oso.seed_known_proxy_contracts,
    kind seed(path '../../seeds/known_proxy_contracts.csv'),
    columns(proxy_type varchar, version varchar, factory_address varchar)
)
;
