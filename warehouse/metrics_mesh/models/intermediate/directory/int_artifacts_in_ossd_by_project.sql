MODEL (
  name metrics.int_artifacts_in_ossd_by_project,
  kind FULL,
);

with projects as (
  select
    project_id,
    websites::JSON as websites,
    social::JSON as social,
    github::JSON as github,
    npm::JSON as npm,
    blockchain::JSON as blockchain
  from @oso_source('bigquery.oso.stg_ossd__current_projects')
),

all_websites as (
  select
    projects.project_id,
    json_extract_string(pw.websites, '$') as artifact_source_id,
    'WWW' as artifact_source,
    'WWW' as artifact_namespace,
    json_extract_string(pw.websites, '$') as artifact_name,
    json_extract_string(pw.websites, '$') as artifact_url,
    'WEBSITE' as artifact_type
  from projects
  cross join
    UNNEST(@json_extract_from_array(projects.websites, '$[*].url')) as pw(websites)
),

all_farcaster as (
  select
    projects.project_id,
    json_extract_string(farcaster, '$') as artifact_source_id,
    'FARCASTER' as artifact_source,
    'FARCASTER' as artifact_namespace,
    json_extract_string(farcaster, '$') as artifact_url,
    'SOCIAL_HANDLE' as artifact_type,
    case
      when
        json_extract_string(farcaster, '$') like 'https://warpcast.com/%'
        then SUBSTR(json_extract_string(farcaster, '$'), 22)
      else json_extract_string(farcaster, '$')
    end as artifact_name
  from projects
  cross join
    UNNEST(@json_extract_from_array(projects.social, '$.farcaster[*].url')) as ps(farcaster)
),

all_twitter as (
  select
    projects.project_id,
    json_extract_string(twitter, '$') as artifact_source_id,
    'TWITTER' as artifact_source,
    'TWITTER' as artifact_namespace,
    json_extract_string(twitter, '$') as artifact_url,
    'SOCIAL_HANDLE' as artifact_type,
    case
      when
        json_extract_string(twitter, '$') like 'https://twitter.com/%'
        then SUBSTR(json_extract_string(twitter, '$'), 21)
      when
        json_extract_string(twitter, '$') like 'https://x.com/%'
        then SUBSTR(json_extract_string(twitter, '$'), 15)
      else json_extract_string(twitter, '$')
    end as artifact_name
  from projects
  cross join
    UNNEST(@json_extract_from_array(projects.social, '$.twitter[*].url')) as ps(twitter)
),

github_repos_raw as (
  select
    projects.project_id,
    'GITHUB' as artifact_source,
    json_extract_string(pg.github, '$') as artifact_url,
    'REPOSITORY' as artifact_type
  from projects
  cross join
    UNNEST(@json_extract_from_array(projects.github, '$[*].url')) as pg(github)
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
    json_extract_string(pn.npm, '$') as artifact_source_id,
    json_extract_string(pn.npm, '$') as artifact_url,
    case
      when
        json_extract_string(pn.npm, '$') like 'https://npmjs.com/package/%'
        then SUBSTR(json_extract_string(pn.npm, '$'), 27)
      when
        json_extract_string(pn.npm, '$') like 'https://www.npmjs.com/package/%'
        then SUBSTR(json_extract_string(pn.npm, '$'), 31)
      else json_extract_string(pn.npm, '$')
    end as artifact_name
  from projects
  cross join
    UNNEST(@json_extract_from_array(projects.npm, '$[*].url')) as pn(npm)
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
    json_extract_string(tag, '$') as artifact_type,
    json_extract_string(network, '$') as artifact_source,
    json_extract_string(blockchains, '$.address') as artifact_source_id,
    json_extract_string(network, '$') as artifact_namespace,
    json_extract_string(blockchains, '$.address') as artifact_name,
    json_extract_string(blockchains, '$.address') as artifact_url
  from projects
  cross join
    UNNEST(@json_extract_from_array(projects.blockchain, '$[*]')) as pb(blockchains)
  cross join
    UNNEST(@json_extract_from_array(blockchains, '$.networks[*]')) as bn(network)
  cross join
    UNNEST(@json_extract_from_array(blockchains, '$.tags[*]')) as bt(tag)
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
