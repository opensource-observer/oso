with url_registry as (
  select
    LOWER(JSON_EXTRACT_SCALAR(to_account, '$.slug')) as project_slug,
    LOWER(JSON_EXTRACT_SCALAR(link, '$.url')) as github_url,
    REGEXP_EXTRACT(LOWER(JSON_EXTRACT_SCALAR(link, '$.url')), r'github\.com/([a-z0-9-]+)')
      as artifact_namespace,
    REGEXP_EXTRACT(
      LOWER(JSON_EXTRACT_SCALAR(link, '$.url')), r'github\.com/[a-z0-9-]+/([a-z0-9-._]+)'
    ) as artifact_name
  from
    {{ ref('stg_open_collective__deposits') }},
    UNNEST(JSON_EXTRACT_ARRAY(to_account, '$.socialLinks')) as link
  where
    JSON_EXTRACT_SCALAR(link, '$.url') like '%github.com%'
),

oso_projects as (
  select
    project_id,
    artifact_namespace,
    artifact_name
  from {{ ref('repositories_v0') }}
  where artifact_source = 'GITHUB'
),

namespace_counts as (
  select
    artifact_namespace,
    COUNT(distinct project_id) as project_count,
    MIN(project_id) as project_id
  from oso_projects
  group by artifact_namespace
),

matched_projects as (
  select
    ur.*,
    case
      when op.project_id is not null then op.project_id
      when nc.project_count = 1 then nc.project_id
    end as project_id
  from url_registry as ur
  left join oso_projects as op
    on
      ur.artifact_namespace = op.artifact_namespace
      and ur.artifact_name = op.artifact_name
  left join namespace_counts as nc
    on ur.artifact_namespace = nc.artifact_namespace
)

select distinct
  project_id as project_id,
  {{ oso_id("'OPEN_COLLECTIVE'", 'project_slug') }} as artifact_id,
  project_slug as artifact_source_id,
  'OPEN_COLLECTIVE' as artifact_source,
  '' as artifact_namespace,
  project_slug as artifact_name,
  'https://opencollective.com/' || project_slug as artifact_url
from matched_projects
