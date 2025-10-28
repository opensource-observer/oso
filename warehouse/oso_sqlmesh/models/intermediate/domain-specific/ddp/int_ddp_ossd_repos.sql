MODEL (
  name oso.int_ddp_ossd_repos,
  description "Repositories from OSSD",
  kind FULL,
  dialect trino,
  grain (artifact_id),
  tags (
    'entity_category=artifact',
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH ranked_repositories AS (
  SELECT
    node_id,
    id,
    LOWER(url) AS url,
    LOWER(name) AS name,
    LOWER(name_with_owner) AS name_with_owner,
    LOWER(owner) AS owner,
    LOWER(branch) AS branch,
    star_count,
    watcher_count,
    fork_count,
    is_fork,
    license_name,
    license_spdx_id,
    language,
    created_at,
    updated_at,
    ingestion_time,
    ROW_NUMBER() OVER (PARTITION BY LOWER(url) ORDER BY ingestion_time DESC, id ASC) AS row_num
  FROM @oso_source('bigquery.ossd.repositories')
),
deduplicated_repositories AS (
  SELECT
    *
  FROM ranked_repositories
  WHERE row_num = 1
)

SELECT
  @oso_entity_id('GITHUB', artifact_fields.artifact_namespace, artifact_fields.artifact_name) AS artifact_id,
  repos.id::TEXT AS artifact_source_id,
  artifact_fields.artifact_source,
  artifact_fields.artifact_namespace,
  artifact_fields.artifact_name,
  artifact_fields.artifact_url,
  artifact_fields.artifact_type,
  repos.node_id,
  repos.url,
  repos.name,
  repos.name_with_owner,
  repos.owner,
  'https://github.com/' || repos.owner AS owner_url,
  repos.is_fork,
  repos.branch,
  repos.star_count,
  repos.watcher_count,
  repos.fork_count,
  repos.license_name,
  repos.license_spdx_id,
  repos.language,
  repos.created_at,
  repos.updated_at,
  repos.ingestion_time
FROM deduplicated_repositories AS repos
CROSS JOIN LATERAL @parse_github_repository_artifact(repos.url) AS artifact_fields