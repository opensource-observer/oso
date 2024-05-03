{#

  This model calculates the bus factor for each project in the database. The bus factor is a metric that
  measures the number of contributors that are responsible for at least 50% of the contributions to a project
  over a given time period. 

  The `contributions` CTE calculates the total amount of contributions for each contributor to each project.
  The `project_periods` CTE calculates the start and end month for each project.
  The `aggregated_contributions` CTE calculates the total amount of contributions for each contributor to each project
  for different time periods (90 days, 6 months, 1 year, and all time).
  The `ranked_contributions` CTE calculates the rank of each contributor for each project and time period, as well as the
  total amount of contributions for each project and time period. The final select statement calculates the bus factor
  for each project and time period by selecting the maximum rank of contributors whose cumulative contributions are
  greater than or equal to 50% of the total contributions to the project.

  More information on the bus factor can be found here: https://chaoss.community/kb/metric-bus-factor/

#}

with all_contributions as (
  select
    project_id,
    from_id,
    SUM(amount) as total_amount,
    DATE_TRUNC(DATE(time), month) as contribution_month
  from {{ ref('int_events_to_project') }}
  where event_type = 'COMMIT_CODE' -- CONTRIBUTION FILTER
  group by
    project_id,
    from_id,
    DATE_TRUNC(DATE(time), month)
),

contributions as (
  select *
  from all_contributions
  where total_amount < 1000 -- BOT FILTER
),

project_periods as (
  select
    project_id,
    MIN(contribution_month) as start_month,
    MAX(contribution_month) as end_month
  from contributions
  group by project_id
),

aggregated_contributions as (
  select
    c.project_id,
    c.from_id,
    SUM(c.total_amount) as total_amount,
    '90D' as period
  from contributions as c
  inner join project_periods as p on c.project_id = p.project_id
  where c.contribution_month > DATE_SUB(p.end_month, interval 3 month)
  group by
    c.project_id,
    c.from_id
  union all
  select
    c.project_id,
    c.from_id,
    SUM(c.total_amount) as total_amount,
    '6M' as period
  from contributions as c
  inner join project_periods as p on c.project_id = p.project_id
  where c.contribution_month > DATE_SUB(p.end_month, interval 6 month)
  group by
    c.project_id,
    c.from_id
  union all
  select
    c.project_id,
    c.from_id,
    SUM(c.total_amount) as total_amount,
    '1Y' as period
  from contributions as c
  inner join project_periods as p on c.project_id = p.project_id
  where c.contribution_month > DATE_SUB(p.end_month, interval 12 month)
  group by
    c.project_id,
    c.from_id
  union all
  select
    c.project_id,
    c.from_id,
    SUM(c.total_amount) as total_amount,
    'ALL' as period
  from contributions as c
  group by
    c.project_id,
    c.from_id
),

ranked_contributions as (
  select
    project_id,
    period,
    from_id,
    total_amount,
    RANK()
      over (
        partition by project_id, period order by total_amount desc
      ) as rank,
    SUM(total_amount)
      over (
        partition by project_id, period
      ) as total_project_amount,
    SUM(total_amount)
      over (
        partition by project_id, period
        order by total_amount desc
        rows between unbounded preceding and current row
      ) as cumulative_amount
  from aggregated_contributions
)

select
  project_id,
  CONCAT('BUSFACTOR_', period) as impact_metric,
  MAX(
    case
      when cumulative_amount <= total_project_amount * 0.5
        then rank
      else 1
    end
  ) as amount
from
  ranked_contributions
group by
  project_id,
  period
