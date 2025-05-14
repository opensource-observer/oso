-- Check for gaps in the date range based on some time interval
AUDIT (
  name no_gaps,
  dialect trino,
  defaults (
    no_gap_date_part = 'day',
    missing_rate_min_threshold = 1.0 -- 1 is 100% of all rows should be present
  ),
);

WITH all_dates AS (
  @date_spine(@no_gap_date_part, @start_ds, @end_ds)
), rows_per_day as (
  SELECT 
    @time_aggregation_bucket(all_dates.date_@{no_gap_date_part}, @no_gap_date_part) as d,
    COUNT(current.@time_column) as num_rows
  FROM all_dates
  LEFT JOIN @this_model AS current
    ON @time_aggregation_bucket(current.@time_column, @no_gap_date_part) = all_dates.date_@{no_gap_date_part}
  WHERE @AND(
    all_dates.date_@{no_gap_date_part} BETWEEN @start_dt AND @end_dt, 
    all_dates.date_@{no_gap_date_part} >= @VAR('ignore_before', '2015-01-01 00:00:00')::TIMESTAMP,
    all_dates.date_@{no_gap_date_part} < NOW() - INTERVAL 1 DAY,
    -- Testing this is hard to do in CI so we effectively disable it
    @testing_enabled IS FALSE
  )
  GROUP BY 1
)
-- An audit fails if a query returns any rows. This will only returns rows if
-- the rate of missing rows is below
SELECT COALESCE(AVG(num_rows), 1.0) AS avg_rows_per_day
FROM rows_per_day
HAVING COALESCE(AVG(num_rows), 1.0) < @missing_rate_min_threshold::FLOAT
