with all_repos as (
  select
    repos.project_id as project_id,
    'GITHUB' as artifact_namespace,
    'GIT_REPOSITORY' as artifact_type,
    LOWER(repos.name_with_owner) as artifact_name,
    LOWER(repos.url) as artifact_url,
    CAST(repos.id as STRING) as artifact_source_id
  from {{ ref('stg_ossd__repositories_by_project') }} as repos
  group by
    1,
    2,
    3,
    4,
    5,
    6
),

all_npm as (
  select
    projects.project_id,
    'NPM' as artifact_namespace,
    'PACKAGE' as artifact_type,
    case
      when
        LOWER(JSON_VALUE(npm.url)) like 'https://npmjs.com/package/%'
        then SUBSTR(LOWER(JSON_VALUE(npm.url)), 28)
      when
        LOWER(
          JSON_VALUE(npm.url)
        ) like 'https://www.npmjs.com/package/%'
        then SUBSTR(LOWER(JSON_VALUE(npm.url)), 31)
    end as artifact_name,
    LOWER(JSON_VALUE(npm.url)) as artifact_url,
    LOWER(JSON_VALUE(npm.url)) as artifact_source_id
  from
    {{ ref('stg_ossd__current_projects') }} as projects
  cross join
    UNNEST(JSON_QUERY_ARRAY(projects.npm)) as npm
),

ossd_blockchain as (
  select
    projects.project_id,
    UPPER(network) as artifact_namespace,
    UPPER(tag) as artifact_type,
    JSON_VALUE(blockchains.address) as artifact_name,
    JSON_VALUE(blockchains.address) as artifact_url,
    JSON_VALUE(blockchains.address) as artifact_source_id
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
    'OPTIMISM' as network
  from {{ ref("stg_optimism__deployers") }}
  union all
  select
    *,
    'MAINNET' as network
  from {{ ref("stg_ethereum__deployers") }}
  union all
  select
    *,
    'ARBITRUM' as network
  from {{ ref("stg_arbitrum__deployers") }}
),

discovered_contracts as (
  select
    ob.project_id,
    ob.artifact_namespace,
    'CONTRACT' as artifact_type,
    ad.contract_address as artifact_name,
    ad.contract_address as artifact_url,
    ad.contract_address as artifact_source_id
  from ossd_blockchain as ob
  inner join all_deployers as ad
    on
      ob.artifact_source_id = ad.deployer_address
      and ob.artifact_namespace = ad.network
      and ob.artifact_type in ('EOA', 'DEPLOYER', 'FACTORY')
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
  select * from all_artifacts group by 1, 2, 3, 4, 5, 6
)

select
  a.*,
  {{ oso_artifact_id("artifact", "a") }} as `artifact_id`
from all_unique_artifacts as a
