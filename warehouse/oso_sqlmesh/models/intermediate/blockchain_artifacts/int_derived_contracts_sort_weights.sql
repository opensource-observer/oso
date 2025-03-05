/* In order to keep this model as small and the least complicated it can be we */ /* take the last 180 days and aggregate activity on a given contract on a weekly */ /* basis when used in the contracts overview model. This model is intermediate */ /* to that model and simply aggregates the transactions on a weekly basis for a */ /* given contract. It only goes back ~6 months from the time we deployed this */ /* model (2025-02-01) */ /* In the future we should make a different model type for this that */ /* automatically deletes _old_ data that we don't need. However sqlmesh doesn't */ /* have out of the box support for that yet so we will implement as an */ /* INCREMENTAL_BY_TIME_RANGE model for now. */
MODEL (
  name oso.int_derived_contracts_sort_weights,
  kind FULL
);

@DEF(start, CURRENT_DATE - INTERVAL '180' DAY);

@DEF(end, CURRENT_DATE);

/* Find all transactions involving the contracts from `derived_contracts` and */ /* aggregate their tx_count on a weekly basis */
SELECT
  UPPER(derived_contracts.chain) AS chain,
  transactions_weekly.contract_address,
  SUM(transactions_weekly.tx_count) AS sort_weight
FROM oso.int_contracts_transactions_weekly AS transactions_weekly
INNER JOIN oso.int_derived_contracts AS derived_contracts
  ON derived_contracts.contract_address = transactions_weekly.contract_address
  AND UPPER(transactions_weekly.chain) = UPPER(derived_contracts.chain)
WHERE
  transactions_weekly.week BETWEEN @start AND @end
GROUP BY
  1,
  2