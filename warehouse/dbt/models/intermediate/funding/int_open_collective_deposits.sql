with open_collective_deposits as (
  select
    id as event_source_id,
    created_at as `time`,
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
),

ocd as (
  select
    event_source_id,
    `time`,
    'DEPOSIT' as event_type,
    'OPEN_COLLECTIVE' as event_source,
    to_project_name,
    LOWER(to_project_slug) as to_project_slug,
    UPPER(to_project_type) as to_project_type,
    UPPER(currency) as currency,
    CAST(amount as numeric) as amount,
    LOWER(github_url) as github_url
  from open_collective_deposits
),

namespace_counts as (
  select
    artifact_namespace,
    COUNT(distinct project_id) as namespace_project_count
  from {{ ref('repositories_v0') }}
  group by artifact_namespace
),

single_project_namespaces as (
  select artifact_namespace
  from namespace_counts
  where namespace_project_count = 1
),

filtered_repos as (
  select repos.*
  from {{ ref('repositories_v0') }} as repos
  inner join single_project_namespaces as spn
    on repos.artifact_namespace = spn.artifact_namespace
),

github_matches as (
  select
    ocd.*,
    repos.project_id as to_project_id
  from ocd
  left join {{ ref('repositories_v0') }} as repos
    on LOWER(ocd.github_url) = repos.artifact_url
),

namespace_matches as (
  select
    ocd.*,
    repos.project_id as to_project_id
  from ocd
  left join filtered_repos as repos
    on REGEXP_EXTRACT(ocd.github_url, 'github.com/([^/]+)', 1) = repos.artifact_namespace
  where ocd.event_source_id not in (
    select event_source_id
    from github_matches
    where to_project_id is not null
  )
),

final as (
  select *
  from github_matches
  where to_project_id is not null
  union all
  select *
  from namespace_matches
  where to_project_id is not null
  union all
  select
    *,
    null as to_project_id
  from ocd
  where event_source_id not in (
    select event_source_id
    from github_matches
    where to_project_id is not null
    union all
    select event_source_id
    from namespace_matches
    where to_project_id is not null
  )
)

select * from final
