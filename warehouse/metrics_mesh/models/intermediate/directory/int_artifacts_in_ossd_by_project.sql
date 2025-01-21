MODEL (
  name metrics.int_artifacts_in_ossd_by_project,
  kind FULL,
);

with projects as (
  select
    project_id,
    websites,
    social,
    github,
    npm,
    blockchain
  from @oso_source('bigquery.oso.stg_ossd__current_projects')
),

all_websites as (
  select
    projects.project_id,
    unnest(json_extract_string(websites, '$.*')) as artifact_source_id,
    'WWW' as artifact_source,
    'WWW' as artifact_namespace,
    artifact_source_id as artifact_name,
    artifact_source_id as artifact_url,
    'WEBSITE' as artifact_type
  from projects
  cross join
    UNNEST(json_extract(projects.websites, '$[*].url')) as websites
),

all_farcaster as (
  select
    projects.project_id,
    unnest(json_extract_string(farcaster, '$.*')) as artifact_source_id,
    'FARCASTER' as artifact_source,
    'FARCASTER' as artifact_namespace,
    artifact_source_id as artifact_url,
    'SOCIAL_HANDLE' as artifact_type,
    case
      when
        artifact_source_id like 'https://warpcast.com/%'
        then SUBSTR(artifact_source_id, 22)
      else artifact_source_id
    end as artifact_name
  from projects
  cross join
    UNNEST(json_extract(projects.social, '$.farcaster[*].url')) as farcaster
),

all_twitter as (
  select
    projects.project_id,
    unnest(json_extract_string(twitter, '$.*')) as artifact_source_id,
    'TWITTER' as artifact_source,
    'TWITTER' as artifact_namespace,
    artifact_source_id as artifact_url,
    'SOCIAL_HANDLE' as artifact_type,
    case
      when
        artifact_source_id like 'https://twitter.com/%'
        then SUBSTR(artifact_source_id, 21)
      when
        artifact_source_id like 'https://x.com/%'
        then SUBSTR(artifact_source_id, 15)
      else artifact_source_id
    end as artifact_name
  from projects
  cross join
    UNNEST(json_extract(projects.social, '$.twitter[*].url')) as twitter
),

github_repos_raw as (
  select
    projects.project_id,
    'GITHUB' as artifact_source,
    unnest(json_extract_string(github, '$.*')) as artifact_url,
    'REPOSITORY' as artifact_type
  from projects
  cross join
    UNNEST(json_extract(projects.github, '$[*].url')) as github
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
    @oso_source('bigquery.oso.stg_ossd__current_repositories') as repos
    on
      {#
        We join on either the repo url or the user/org url.
        The RTRIMs are to ensure we match even if there are trailing slashes 
      #}
      LOWER(CONCAT('https://github.com/', repos.owner))
        = LOWER(RTRIM(artifact_url, '/'))
      or LOWER(repos.url) = LOWER(RTRIM(artifact_url, '/'))
),

all_npm_raw as (
  select
    'NPM' as artifact_source,
    'PACKAGE' as artifact_type,
    projects.project_id,
    unnest(json_extract_string(npm, '$.*')) as artifact_source_id,
    artifact_source_id as artifact_url,
    case
      when
        artifact_source_id like 'https://npmjs.com/package/%'
        then SUBSTR(artifact_source_id, 27)
      when
        artifact_source_id like 'https://www.npmjs.com/package/%'
        then SUBSTR(artifact_source_id, 31)
      else artifact_source_id
    end as artifact_name
  from projects
  cross join
    UNNEST(json_extract(projects.npm, '$[*].url')) as npm
),

all_npm as (
  select
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_name,
    artifact_url,
    SPLIT(REPLACE(artifact_name, '@', ''), '/')[0]
      as artifact_namespace
  from all_npm_raw
),

ossd_blockchain as (
  select
    projects.project_id,
    unnest(json_extract_string(tag, '$.*')) as artifact_type,
    unnest(json_extract_string(network, '$.*')) as artifact_source,
    unnest(json_extract_string(blockchains, '$.*.address')) as artifact_source_id,
    artifact_source as artifact_namespace,
    artifact_source_id as artifact_name,
    artifact_source_id as artifact_url
  from projects
  cross join
    UNNEST(json_extract(projects.blockchain, '$[*]')) as blockchains
  cross join
    UNNEST(json_extract(blockchains, '$.*.networks[*]')) as network
  cross join
    UNNEST(json_extract(blockchains, '$.*.tags[*]')) as tag
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
    {# 
      artifact_source and artifact_type are considered internal constants hence
      we apply an UPPER transform
    #}
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
