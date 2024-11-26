with npm_artifacts as (
  select artifact_name
  from {{ ref('artifacts_v1') }}
  where artifact_source = 'NPM'
),

npm_manifests as (
  select
    `name`,
    json_value(repository, '$.url') as manifest_repository_url,
    json_value(repository, '$.type') as manifest_repository_type,
    concat('https://www.npmjs.com/package/', `name`) as artifact_url
  from {{ ref('stg_npm__manifests') }}
  where
    `name` in (select * from npm_artifacts)
    and json_value(repository, '$.url') is not null
),

npm_repository_urls as (
  {{ parse_npm_git_url('manifest_repository_url', 'npm_manifests') }}
),

npm_artifact_ownership as (
  select
    {{ oso_id(
      "'NPM'",
      "artifact_url",
    ) }} as artifact_id,
    artifact_url,
    `name` as artifact_name,
    'NPM' as artifact_source_id,
    remote_url,
    remote_name,
    remote_namespace,
    remote_source_id
  from npm_repository_urls
)

select * from npm_artifact_ownership
