with dates as (
  select
    '7 DAYS' as time_interval,
    DATE_SUB(CURRENT_DATE(), interval 7 day) as start_date
  union all
  select
    '30 DAYS' as time_interval,
    DATE_SUB(CURRENT_DATE(), interval 30 day) as start_date
  union all
  select
    '90 DAYS' as time_interval,
    DATE_SUB(CURRENT_DATE(), interval 90 day) as start_date
  union all
  select
    '6 MONTHS' as time_interval,
    DATE_SUB(CURRENT_DATE(), interval 6 month) as start_date
  union all
  select
    '1 YEAR' as time_interval,
    DATE_SUB(CURRENT_DATE(), interval 1 year) as start_date
  union all
  select
    'ALL' as time_interval,
    DATE('1970-01-01') as start_date
)

select
  dates.time_interval,
  TIMESTAMP(dates.start_date) as start_date
from dates
