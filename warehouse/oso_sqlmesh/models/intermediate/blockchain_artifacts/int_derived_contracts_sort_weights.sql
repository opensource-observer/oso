-- In order to keep this model as small and the least complicated it can be we
-- take the last 180 days and aggregate activity on a given contract on a weekly
-- basis when used in the contracts overview model. This model is intermediate
-- to that model and simply aggregates the transactions on a weekly basis for a
-- given contract. It only goes back ~6 months from the time we deployed this
-- model (2025-02-01)
-- In the future we should make a different model type for this that
-- automatically deletes _old_ data that we don't need. However sqlmesh doesn't
-- have out of the box support for that yet so we will implement as an
-- INCREMENTAL_BY_TIME_RANGE model for now.
model(name oso.int_derived_contracts_sort_weights, kind full)
;

@def(start, current_date() - interval 180 day)
;
@def(end, current_date())
;

-- Find all transactions involving the contracts from `derived_contracts` and
-- aggregate their tx_count on a weekly basis
select
    upper(derived_contracts.chain) as chain,
    transactions_weekly.contract_address,
    sum(transactions_weekly.tx_count) as sort_weight
from oso.int_contracts_transactions_weekly as transactions_weekly
inner join
    oso.int_derived_contracts as derived_contracts
    on derived_contracts.contract_address = transactions_weekly.contract_address
    and upper(transactions_weekly.chain) = upper(derived_contracts.chain)
where transactions_weekly.week between @start and @end
group by 1, 2
