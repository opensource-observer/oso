with open_collective_deposits as (
  select
    id as event_source_id,
    created_at as `time`,
    'DEPOSIT' as event_type,
    'OPEN_COLLECTIVE' as event_source,
    JSON_EXTRACT_SCALAR(to_account, '$.name') as to_project_name,
    JSON_EXTRACT_SCALAR(to_account, '$.slug') as to_project_slug,
    JSON_EXTRACT_SCALAR(to_account, '$.type') as to_project_type,
    JSON_EXTRACT_SCALAR(amount, '$.currency') as currency,
    JSON_EXTRACT_SCALAR(amount, '$.value') as amount,
    JSON_EXTRACT_SCALAR(link, '$.url') as github_url
  from
    {{ ref('stg_open_collective__deposits') }},
    UNNEST(JSON_EXTRACT_ARRAY(to_account, '$.socialLinks')) as link
  where
    JSON_EXTRACT_SCALAR(link, '$.url') like '%github.com%'
)

select *
from open_collective_deposits
