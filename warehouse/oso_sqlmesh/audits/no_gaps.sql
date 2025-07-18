-- Check for gaps in the date range based on some time interval
AUDIT (
  name no_gaps,
  dialect trino,
  defaults (
    no_gap_date_part = 'day',
    missing_rate_min_threshold = 1.0, -- 1 is 100% of all rows should be present
    ignore_before = '2015-01-01 00:00:00',
    ignore_after = 'now',
  ),
);

WITH all_dates AS (
  @date_spine(@no_gap_date_part, @start_ds, @end_ds)
), rows_per_day as (
  SELECT
    @time_aggregation_bucket(all_dates.date_@{no_gap_date_part}, @no_gap_date_part) as d,
    CASE 
      WHEN COUNT(current.@time_column) >= 1 THEN 1.0 
      ELSE 0.0
    END as has_rows
  FROM all_dates
  LEFT JOIN @this_model AS current
    ON @time_aggregation_bucket(current.@time_column, @no_gap_date_part) = all_dates.date_@{no_gap_date_part}
  WHERE @AND(
    all_dates.date_@{no_gap_date_part} BETWEEN @start_dt AND @end_dt,
    all_dates.date_@{no_gap_date_part} >= @ignore_before::TIMESTAMP,
    @IF(
      @ignore_after != 'now', 
      -- If ignore_after is set, we ignore rows after that date 
      all_dates.date_@{no_gap_date_part} <= @ignore_after::TIMESTAMP, 
      -- By default we give late data a 2-day grace period to arrive
      all_dates.date_@{no_gap_date_part} < NOW() - INTERVAL 2 DAY,
    ),
    -- Testing this is hard to do in CI so we effectively disable it
    @testing_enabled IS FALSE
  )
  GROUP BY 1
)
-- An audit fails if a query returns any rows. This will only returns rows if
-- the rate of missing rows is below
SELECT COALESCE(AVG(has_rows), 1.0) AS avg_rows_per_day
FROM rows_per_day
HAVING COALESCE(AVG(has_rows), 1.0) < @missing_rate_min_threshold::FLOAT
