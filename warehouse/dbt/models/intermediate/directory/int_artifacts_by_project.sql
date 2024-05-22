{#
  This model is responsible for generating a list of all artifacts associated with a project.
  This includes repositories, npm packages, blockchain addresses, and contracts.

  Currently, the source and namespace for blockchain artifacts are the same. This may change
  in the future.
#}

with all_repos as (
  {#
    Currently this is just Github.
    oss-directory needs some refactoring to support multiple repository providers
  #}
  select
    "GITHUB" as artifact_source,
    "REPOSITORY" as artifact_type,
    projects.project_id,
    repos.owner as artifact_namespace,
    repos.name as artifact_name,
    repos.url as artifact_url,
    CAST(repos.id as STRING) as artifact_source_id
  from
    {{ ref('stg_ossd__current_projects') }} as projects
  cross join
    UNNEST(JSON_QUERY_ARRAY(projects.github)) as github
  inner join
    {{ ref('stg_ossd__current_repositories') }} as repos
    on
      LOWER(CONCAT("https://github.com/", repos.owner))
      = LOWER(JSON_VALUE(github.url))
      or LOWER(repos.url) = LOWER(JSON_VALUE(github.url))
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
    projects.project_id,
    tag as artifact_type,
    network as artifact_namespace,
    network as artifact_source,
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
    "MAINNET" as artifact_namespace,
    "ETHEREUM" as artifact_source
  from {{ ref("stg_ethereum__deployers") }}
  union all
  select
    *,
    "ARBITRUM_ONE" as artifact_namespace,
    "ARBITRUM_ONE" as artifact_source
  from {{ ref("stg_arbitrum__deployers") }}
  union all
  select
    block_timestamp,
    transaction_hash,
    deployer_address,
    contract_address,
    UPPER(network) as artifact_namespace,
    UPPER(network) as artifact_source
  from {{ ref("int_derived_contracts") }}
),

discovered_contracts as (
  select
    "CONTRACT" as artifact_type,
    ob.project_id,
    ad.contract_address as artifact_source_id,
    ob.artifact_namespace,
    ob.artifact_namespace as artifact_source,
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
  select
    project_id,
    artifact_source_id,
    artifact_source,
    artifact_type,
    artifact_namespace,
    artifact_name,
    artifact_url
  from
    all_repos
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
    discovered_contracts
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

all_unique_artifacts as (
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
  artifact_source_id,
  artifact_source,
  artifact_type,
  artifact_namespace,
  artifact_name,
  artifact_url,
  {{ oso_id("a.artifact_source", "a.artifact_source_id") }} as `artifact_id`
from all_unique_artifacts as a
