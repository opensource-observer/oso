-- Check for gaps in the date range based on some time interval
AUDIT (
  name no_gaps,
  dialect trino,
  defaults (
    no_gap_date_part = 'day'
  ),
);

WITH all_dates AS (
  @date_spine(@no_gap_date_part, @start_ds, @end_ds)
)

SELECT 
  @time_bucket_aggregation(all_dates.date_@{no_gap_date_part}, @no_gap_date_part) as d,
  COUNT(current.@time_column) as num_rows
FROM all_dates
LEFT JOIN @this_model AS current
  ON @time_bucket_aggregation(current.@time_column, @no_gap_date_part) = all_dates.date_@{no_gap_date_part}
WHERE @AND(
  all_dates.date_@{no_gap_date_part} BETWEEN @start_dt AND @end_dt, 
  all_dates.date_@{no_gap_date_part} >= @VAR('ignore_before', '2015-01-01 00:00:00')::TIMESTAMP,
  all_dates.date_@{no_gap_date_part} < NOW() - INTERVAL 1 DAY,
  -- Testing this is hard to do in CI so we effectively disable it
  @testing_enabled IS FALSE
)
GROUP BY 1
HAVING COUNT(current.@time_column) = 0