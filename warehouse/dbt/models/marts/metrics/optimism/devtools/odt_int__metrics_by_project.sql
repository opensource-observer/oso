with metrics as (
  select * from {{ ref('odt_metric__total_dependents') }}
),

pivoted as (
  select
    project_id,
    SUM(case when metric = 'total_dependents' then amount else 0 end)
      as total_dependents
  from metrics
  group by project_id
)

select * from pivoted
