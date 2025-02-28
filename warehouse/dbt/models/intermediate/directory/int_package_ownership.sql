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
      "artifact_source",
      "artifact_url",
    ) }} as artifact_id,
    artifact_url as artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    remote_artifact_source,
    remote_artifact_namespace,
    remote_artifact_name,
    remote_artifact_url
  from npm_repository_urls
)

select
  npm_artifact_ownership.artifact_id,
  npm_artifact_ownership.artifact_source_id,
  npm_artifact_ownership.artifact_source,
  npm_artifact_ownership.artifact_namespace,
  npm_artifact_ownership.artifact_name,
  npm_artifact_ownership.artifact_url,
  {#
    Because we use repo.id as the artifact_source_id for github, we need to lookup the artifact_id for the remote artifact. If the artifact is not found, this will return null.
  #}
  all_artifacts.artifact_id as remote_artifact_id,
  npm_artifact_ownership.remote_artifact_source,
  npm_artifact_ownership.remote_artifact_namespace,
  npm_artifact_ownership.remote_artifact_name,
  npm_artifact_ownership.remote_artifact_url
from npm_artifact_ownership
left outer join {{ ref('int_all_artifacts') }} as all_artifacts
  on
    npm_artifact_ownership.remote_artifact_namespace = all_artifacts.artifact_namespace
    and npm_artifact_ownership.remote_artifact_name = all_artifacts.artifact_name
