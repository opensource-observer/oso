with all_repos as (
  select
    "GITHUB" as artifact_source,
    "GIT_REPOSITORY" as artifact_type,
    repos.project_id as project_id,
    repos.owner as artifact_namespace,
    repos.name_with_owner as artifact_name,
    repos.url as artifact_url,
    CAST(repos.id as STRING) as artifact_source_id
  from {{ ref('int_ossd__repositories_by_project') }} as repos
),

all_npm_raw as (
  select
    "NPM" as artifact_source,
    "PACKAGE" as artifact_type,
    projects.project_id,
    JSON_VALUE(npm.url) as artifact_source_id,
    case
      when
        JSON_VALUE(npm.url) like "https://npmjs.com/package/%"
        then SUBSTR(JSON_VALUE(npm.url), 28)
      when
        JSON_VALUE(npm.url) like "https://www.npmjs.com/package/%"
        then SUBSTR(JSON_VALUE(npm.url), 31)
    end as artifact_name,
    JSON_VALUE(npm.url) as artifact_url
  from
    {{ ref('stg_ossd__current_projects') }} as projects
  cross join
    UNNEST(JSON_QUERY_ARRAY(projects.npm)) as npm
),

all_npm as (
  select
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_name,
    artifact_url,
    SPLIT(REPLACE(artifact_name, "@", ""), "/")[SAFE_OFFSET(0)]
      as artifact_namespace
  from all_npm_raw
),

ossd_blockchain as (
  select
    "EVM" as artifact_source,
    projects.project_id,
    tag as artifact_type,
    network as artifact_namespace,
    JSON_VALUE(blockchains.address) as artifact_source_id,
    JSON_VALUE(blockchains.address) as artifact_name,
    JSON_VALUE(blockchains.address) as artifact_url
  from
    {{ ref('stg_ossd__current_projects') }} as projects
  cross join
    UNNEST(JSON_QUERY_ARRAY(projects.blockchain)) as blockchains
  cross join
    UNNEST(JSON_VALUE_ARRAY(blockchains.networks)) as network
  cross join
    UNNEST(JSON_VALUE_ARRAY(blockchains.tags)) as tag
),

all_deployers as (
  select
    *,
    "OPTIMISM" as artifact_namespace,
    "EVM" as artifact_source
  from {{ ref("stg_optimism__deployers") }}
  union all
  select
    *,
    "MAINNET" as artifact_namespace,
    "EVM" as artifact_source
  from {{ ref("stg_ethereum__deployers") }}
  union all
  select
    *,
    "ARBITRUM" as artifact_namespace,
    "EVM" as artifact_source
  from {{ ref("stg_arbitrum__deployers") }}
),

discovered_contracts as (
  select
    "EVM" as artifact_source,
    "CONTRACT" as artifact_type,
    ob.project_id,
    ad.contract_address as artifact_source_id,
    ob.artifact_namespace,
    ad.contract_address as artifact_name,
    ad.contract_address as artifact_url
  from ossd_blockchain as ob
  inner join all_deployers as ad
    on
      ob.artifact_source_id = ad.deployer_address
      and ob.artifact_namespace = ad.artifact_namespace
      and ob.artifact_type in ("EOA", "DEPLOYER", "FACTORY")
),

all_artifacts as (
  select *
  from
    all_repos
  union all
  select *
  from
    ossd_blockchain
  union all
  select *
  from
    discovered_contracts
  union all
  select *
  from
    all_npm
),

all_unique_artifacts as (
  select distinct
    project_id,
    LOWER(artifact_source_id) as artifact_source_id,
    UPPER(artifact_source) as artifact_source,
    UPPER(artifact_type) as artifact_type,
    UPPER(artifact_namespace) as artifact_namespace,
    LOWER(artifact_name) as artifact_name,
    LOWER(artifact_url) as artifact_url
  from all_artifacts
)

select
  a.*,
  {{ oso_artifact_id("artifact", "a") }} as `artifact_id`
from all_unique_artifacts as a
