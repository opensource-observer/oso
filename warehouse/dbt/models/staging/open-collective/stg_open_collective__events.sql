with open_collective_expenses as (
  select * from {{ open_collective_events("stg_open_collective__expenses") }}
),

open_collective_deposits as (
  select * from {{ open_collective_events("stg_open_collective__deposits") }}
)

select * from open_collective_expenses
union all
select * from open_collective_deposits
