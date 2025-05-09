AUDIT (
  name no_gaps,
  dialect trino
);

WITH all_dates AS (
  @date_spine(@audit_date_part, @start_ds, @end_ds)
)

SELECT 
  date_trunc(@audit_date_part, @time_column) as d,
  COUNT(*) as num_rows
FROM @this_model
RIGHT JOIN all_dates 
  ON date_trunc(@audit_date_part, @time_column) = all_dates.date_day
WHERE @AND(
  @time_column BETWEEN @start_dt AND @end_dt, 
  @time_column < @VAR('ignore_before'),
  @time_column >= @VAR('ignore_after'),
)
HAVING COUNT(*) = 0