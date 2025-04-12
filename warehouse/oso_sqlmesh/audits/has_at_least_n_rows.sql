AUDIT (
  name has_at_least_n_rows,
  dialect duckdb

);

with num_rows as (
  select count(*) as amount from @this_model
)
-- Yield no rows if audit passes
-- Yield 1 row (count) if audit fails
select amount from num_rows where amount < @threshold
