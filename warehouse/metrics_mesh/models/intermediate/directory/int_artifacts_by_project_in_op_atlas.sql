MODEL (
  name metrics.int_artifacts_by_project_in_op_atlas,
  kind FULL,
  dialect trino
);

with all_websites as (
  select
    links.project_id,
    links.artifact_source_id,
    'WWW' as artifact_source,
    'WWW' as artifact_namespace,
    links.artifact_url as artifact_name,
    links.artifact_url
    'WEBSITE' as artifact_type
  from metrics.stg_op_atlas_project_links as links
),

all_twitter as (
  select
    projects.project_id,
    projects.project_source_id as artifact_source_id,
    'TWITTER' as artifact_source,
    'TWITTER' as artifact_namespace,
    projects.twitter as artifact_url,
    'SOCIAL_HANDLE' as artifact_type,
    case
      when
        projects.twitter like 'https://twitter.com/%'
        then SUBSTR(projects.twitter, 21)
      when
        projects.twitter like 'https://x.com/%'
        then SUBSTR(projects.twitter, 15)
      else projects.twitter
    end as artifact_name
  from metrics.stg_op_atlas_project as projects
),

github_repos_raw as (
  select
    projects.project_id,
    'GITHUB' as artifact_source,
    unnested_github.url as artifact_url,
    'REPOSITORY' as artifact_type
  from projects
  cross join
    UNNEST(projects.github) as @unnested_struct_ref(unnested_github)
),

github_repos as (
  select
    project_id,
    artifact_source,
    CAST(repos.id as STRING) as artifact_source_id,
    repos.owner as artifact_namespace,
    repos.name as artifact_name,
    artifact_url,
    artifact_type
  from github_repos_raw
  inner join
    metrics.stg_ossd__current_repositories as repos
    on
      {#
        We join on either the repo url or the user/org url.
        The RTRIMs are to ensure we match even if there are trailing slashes 
      #}
      LOWER(CONCAT('https://github.com/', repos.owner))
        = LOWER(RTRIM(artifact_url, '/'))
      or LOWER(repos.url) = LOWER(RTRIM(artifact_url, '/'))
),

all_contracts as (
  select
    contracts.project_id,
    contracts.artifact_source_id as artifact_source_id,
    unnested_network as artifact_source,
    unnested_network as artifact_namespace,
    contracts.contract_address as artifact_name,
    NULL as artifact_type,
    contracts.contract_address as artifact_url
  from metrics.stg_op_atlas_project_contract as contracts
),

all_artifacts as (
  select
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  from
    all_websites
  union all
  select
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  from
    all_farcaster
  union all
  select
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  from
    all_twitter
  union all
  select
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  from
    github_repos
  union all
  select
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  from
    ossd_blockchain
  union all
  select
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  from
    all_npm
),

all_normalized_artifacts as (
  select distinct
    project_id,
    LOWER(artifact_source_id) as artifact_source_id,
    UPPER(artifact_source) as artifact_source,
    UPPER(artifact_type) as artifact_type,
    LOWER(artifact_namespace) as artifact_namespace,
    LOWER(artifact_name) as artifact_name,
    LOWER(artifact_url) as artifact_url
  from all_artifacts
)

select
  project_id,
  @oso_id(artifact_source, artifact_source_id) as artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url,
  artifact_type
from all_normalized_artifacts
