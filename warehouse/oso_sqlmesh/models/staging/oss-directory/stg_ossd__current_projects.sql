MODEL (
  name oso.stg_ossd__current_projects,
  description 'The most recent view of projects from the ossd dagster source',
  dialect trino,
  kind FULL,
  audits (
    number_of_rows(threshold := 0)
  )
);

SELECT
  @oso_entity_id('OSS_DIRECTORY', 'oso', name) AS project_id, /* id is the SHA256 of namespace + slug */ /* We hardcode our namespace "oso" for now */ /* but we are assuming we will allow users to add their on the OSO website */
  'OSS_DIRECTORY' AS project_source,
  'oso' AS project_namespace,
  LOWER(projects.name) AS project_name,
  projects.display_name,
  projects.description,
  projects.websites,
  projects.social,
  projects.github,
  projects.npm,
  projects.pypi,
  projects.crates,
  projects.go,
  projects.blockchain,
  projects.defillama,
  projects.open_collective,
  projects.sha,
  projects.committed_time
FROM @oso_source('bigquery.ossd.projects') AS projects
