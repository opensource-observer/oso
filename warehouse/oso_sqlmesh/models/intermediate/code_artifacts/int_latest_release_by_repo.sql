MODEL (
  name oso.int_latest_release_by_repo,
  kind FULL,
  enabled false
);

WITH repo_releases AS (
  SELECT
    to_artifact_id AS artifact_id,
    MAX("time") AS latest_repo_release
  FROM oso.int_events__github
  WHERE
    event_type = 'RELEASE_PUBLISHED'
  GROUP BY
    to_artifact_id
), package_releases AS (
  SELECT
    package_github_artifact_id AS artifact_id,
    MAX(snapshot_at) AS latest_package_release
  FROM oso.int_sbom_artifacts
  GROUP BY
    package_github_artifact_id
)
SELECT DISTINCT
  COALESCE(r.artifact_id, p.artifact_id) AS artifact_id,
  COALESCE(r.latest_repo_release, p.latest_package_release) AS last_release_published,
  CASE
    WHEN NOT r.latest_repo_release IS NULL
    THEN 'GITHUB_RELEASE'
    ELSE 'PACKAGE_SNAPSHOT'
  END AS last_release_source
FROM repo_releases AS r
FULL OUTER JOIN package_releases AS p
  ON r.artifact_id = p.artifact_id
WHERE
  NOT COALESCE(r.latest_repo_release, p.latest_package_release) IS NULL