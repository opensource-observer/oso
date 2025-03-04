model(
    name oso.int_contracts_deployment,
    kind incremental_by_time_range(
        time_column deployment_timestamp, batch_size 90, batch_concurrency 1,
    -- forward_only true,
    -- on_destructive_change warn
    ),
    start '2021-10-01',
    partitioned_by(day("deployment_timestamp"), "chain"),
)
;

-- The intent is to get the _first_ factory deployments as some contracts
-- deployed via deterministic deployers allows for multiple calls to the
-- create2 function.
with
    ordered_deployments_in_period as (
        select
            factories.block_timestamp as deployment_timestamp,
            factories.chain as chain,
            factories.transaction_hash as transaction_hash,
            case
                when proxies.address is not null
                then proxies.address
                else factories.originating_address
            end as originating_address,
            factories.originating_contract as originating_contract,
            factories.contract_address as contract_address,
            factories.factory_address as factory_address,
            factories.create_type,
            row_number() over (
                partition by factories.contract_address, factories.chain
                order by block_timestamp asc
            ) as creation_order,
            case when proxies.address is not null then true else false end as is_proxy
        from oso.int_factories as factories
        left join
            oso.int_proxies as proxies
            on factories.originating_contract = proxies.address
            and factories.chain = proxies.chain
        where
            contract_address is not null
            and block_timestamp between @start_dt and @end_dt
            -- ignore anything that already has already been processed
            and contract_address not in (
                select contract_address
                from @this_model
                where block_timestamp < @start_dt
            )
    )
select
    deployment_timestamp::timestamp,
    chain::varchar,
    transaction_hash::varchar,
    originating_address::varchar,
    contract_address::varchar,
    factory_address::varchar,
    create_type::varchar,
    is_proxy::boolean
from ordered_deployments_in_period
where creation_order = 1
