select
  '30D' as time_interval,
  DATE_SUB(CURRENT_DATE(), interval 30 day) as start_date
union all
select
  '90D' as time_interval,
  DATE_SUB(CURRENT_DATE(), interval 90 day) as start_date
union all
select
  '6M' as time_interval,
  DATE_SUB(CURRENT_DATE(), interval 6 month) as start_date
union all
select
  '1Y' as time_interval,
  DATE_SUB(CURRENT_DATE(), interval 1 year) as start_date
union all
select
  'ALL' as time_interval,
  DATE('1970-01-01') as start_date
