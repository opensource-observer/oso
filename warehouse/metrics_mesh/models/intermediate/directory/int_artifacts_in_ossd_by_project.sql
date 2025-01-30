MODEL (
  name metrics.int_artifacts_in_ossd_by_project,
  kind FULL,
  dialect trino
);

with projects as (
  select
    project_id,
    websites as websites,
    social as social,
    github as github,
    npm as npm,
    blockchain as blockchain
  from @oso_source('bigquery.oso.stg_ossd__current_projects')
),

all_websites as (
  select
    projects.project_id,
    pw.websites as artifact_source_id,
    'WWW' as artifact_source,
    'WWW' as artifact_namespace,
    pw.websites as artifact_name,
    pw.websites as artifact_url,
    'WEBSITE' as artifact_type
  from projects
  cross join
    UNNEST(projects.websites) as pw(websites)
),

all_farcaster as (
  select
    projects.project_id,
    ps.farcaster as artifact_source_id,
    'FARCASTER' as artifact_source,
    'FARCASTER' as artifact_namespace,
    ps.farcaster as artifact_url,
    'SOCIAL_HANDLE' as artifact_type,
    case
      when
        ps.farcaster like 'https://warpcast.com/%'
        then SUBSTR(ps.farcaster, 22)
      else ps.farcaster
    end as artifact_name
  from projects
  cross join
    UNNEST(projects.social.farcaster) as ps(farcaster)
),

all_twitter as (
  select
    projects.project_id,
    ps.twitter as artifact_source_id,
    'TWITTER' as artifact_source,
    'TWITTER' as artifact_namespace,
    ps.twitter as artifact_url,
    'SOCIAL_HANDLE' as artifact_type,
    case
      when
        ps.twitter like 'https://twitter.com/%'
        then SUBSTR(twitter, 21)
      when
        ps.twitter like 'https://x.com/%'
        then SUBSTR(ps.twitter, 15)
      else ps.twitter
    end as artifact_name
  from projects
  cross join
    UNNEST(projects.social.twitter) as ps(twitter)
),

github_repos_raw as (
  select
    projects.project_id,
    'GITHUB' as artifact_source,
    pg.github as artifact_url,
    'REPOSITORY' as artifact_type
  from projects
  cross join
    UNNEST(projects.github) as pg(github)
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
    pn.npm as artifact_source_id,
    pn.npm as artifact_url,
    case
      when
        pn.npm like 'https://npmjs.com/package/%'
        then SUBSTR(pn.npm, 27)
      when
        pn.npm like 'https://www.npmjs.com/package/%'
        then SUBSTR(pn.npm, 31)
      else pn.npm
    end as artifact_name
  from projects
  cross join
    UNNEST(projects.npm) as pn(npm)
),

all_npm as (
  select
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_name,
    artifact_url,
    SPLIT(REPLACE(artifact_name, '@', ''), '/')[@array_index(0)]
      as artifact_namespace
  from all_npm_raw
),

ossd_blockchain as (
  select
    projects.project_id,
    tag as artifact_type,
    network as artifact_source,
    address as artifact_source_id,
    network as artifact_namespace,
    address as artifact_name,
    address as artifact_url
  from projects
  cross join
    UNNEST(projects.blockchain) as pb(address, name, networks, tags)
  cross join
    UNNEST(pb.networks) as bn(network)
  cross join
    UNNEST(pb.tags) as bt(tag)
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
