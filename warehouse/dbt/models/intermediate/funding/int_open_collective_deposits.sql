with open_collective_deposits as (
  select
    id as event_source_id,
    created_at as `time`,
    JSON_EXTRACT_SCALAR(to_account, '$.name') as project_name,
    LOWER(JSON_EXTRACT_SCALAR(to_account, '$.slug')) as project_slug,
    UPPER(JSON_EXTRACT_SCALAR(to_account, '$.type')) as project_type,
    UPPER(JSON_EXTRACT_SCALAR(amount, '$.currency')) as currency,
    CAST(JSON_EXTRACT_SCALAR(amount, '$.value') as NUMERIC) as amount
  from {{ ref('stg_open_collective__deposits') }}
)

select
  open_collective_deposits.event_source_id,
  open_collective_deposits.`time`,
  projects.project_id,
  open_collective_deposits.project_name,
  open_collective_deposits.project_slug,
  open_collective_deposits.project_type,
  open_collective_deposits.currency,
  open_collective_deposits.amount
from open_collective_deposits
left join {{ ref('int_open_collective_projects') }} as projects
  on open_collective_deposits.project_slug = projects.artifact_source_id
