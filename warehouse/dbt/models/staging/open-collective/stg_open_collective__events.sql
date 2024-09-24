with open_collective_expenses as (
  select *
  from {{ open_collective_events("stg_open_collective__expenses") }}
  where JSON_VALUE(amount, "$.currency") = "USD"
),

open_collective_deposits as (
  select *
  from {{ open_collective_events("stg_open_collective__deposits") }}
  where JSON_VALUE(amount, "$.currency") = "USD"
)

select * from open_collective_expenses
union all
select * from open_collective_deposits
