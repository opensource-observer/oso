MODEL (
  name oso.int_sbom_package_state_change_events,
  description 'Events tracking the lifecycle of dependencies (add, upgrade, remove) based on SBOM snapshots',
  kind FULL,
  dialect trino,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH raw_extracted AS (
  SELECT
    dependent_artifact_id,
    package_artifact_id,
    snapshot_at,
    package_version,
    @semver_extract(package_version, 'major') AS major,
    @semver_extract(package_version, 'minor') AS minor,
    @semver_extract(package_version, 'patch') AS patch
  FROM oso.int_sbom_from_ossd
),
base_raw AS (
  SELECT
    dependent_artifact_id,
    package_artifact_id,
    snapshot_at,
    package_version,
    major,
    minor,
    patch
  FROM (
    SELECT
      *,
      ROW_NUMBER() OVER(
        PARTITION BY dependent_artifact_id, package_artifact_id, snapshot_at
        ORDER BY major DESC, minor DESC, patch DESC, package_version DESC
      ) AS rn
    FROM raw_extracted
  )
  WHERE rn = 1
),
-- Keep only the LAST snapshot per month per dependent+package+version
monthly_base AS (
  SELECT * FROM (
    SELECT
      br.*,
      DATE_TRUNC('month', br.snapshot_at) AS month_bucket,
      ROW_NUMBER() OVER(
        PARTITION BY br.dependent_artifact_id, br.package_artifact_id, br.package_version, DATE_TRUNC('month', br.snapshot_at)
        ORDER BY br.snapshot_at DESC
      ) AS rn_month
    FROM base_raw AS br
  )
  WHERE rn_month=1
),
dependent_snapshots AS (
  SELECT DISTINCT dependent_artifact_id, snapshot_at FROM monthly_base
),
dependent_snapshots_seq AS (
  SELECT
    dependent_artifact_id,
    snapshot_at,
    LEAD(snapshot_at) OVER(PARTITION BY dependent_artifact_id ORDER BY snapshot_at) AS next_snapshot_at
  FROM dependent_snapshots
),
presence_seq AS (
  SELECT
    p.dependent_artifact_id,
    p.package_artifact_id,
    p.package_version,
    p.snapshot_at,
    p.major,
    p.minor,
    p.patch,
    ROW_NUMBER() OVER(PARTITION BY dependent_artifact_id, package_artifact_id ORDER BY snapshot_at) AS rn,
    LAG(package_version) OVER(PARTITION BY dependent_artifact_id, package_artifact_id ORDER BY snapshot_at) AS prev_version,
    LAG(major) OVER(PARTITION BY dependent_artifact_id, package_artifact_id ORDER BY snapshot_at) AS prev_major,
    LAG(minor) OVER(PARTITION BY dependent_artifact_id, package_artifact_id ORDER BY snapshot_at) AS prev_minor,
    LAG(patch) OVER(PARTITION BY dependent_artifact_id, package_artifact_id ORDER BY snapshot_at) AS prev_patch,
    LEAD(snapshot_at) OVER(PARTITION BY dependent_artifact_id, package_artifact_id ORDER BY snapshot_at) AS next_seen_at
  FROM monthly_base AS p
),
adds AS (
  SELECT
    'ADD_DEPENDENCY' AS event_type,
    snapshot_at AS event_time,
    dependent_artifact_id,
    package_artifact_id,
    CAST(NULL AS varchar) AS version_before,
    package_version AS version_after
  FROM presence_seq
  WHERE rn=1
),
upgrades AS (
  SELECT
    'UPGRADE_DEPENDENCY' AS event_type,
    snapshot_at AS event_time,
    dependent_artifact_id,
    package_artifact_id,
    prev_version AS version_before,
    package_version AS version_after
  FROM presence_seq
  WHERE prev_version IS NOT NULL
    AND package_version <> prev_version
    AND (
      major > prev_major
      OR (major = prev_major AND minor > prev_minor)
      OR (major = prev_major AND minor = prev_minor AND patch > prev_patch)
    )
),
removals AS (
  SELECT
    'REMOVE_DEPENDENCY' AS event_type,
    ds.next_snapshot_at AS event_time,
    ps.dependent_artifact_id,
    ps.package_artifact_id,
    ps.package_version AS version_before,
    CAST(NULL AS varchar) AS version_after
  FROM presence_seq AS ps
  JOIN dependent_snapshots_seq AS ds
    ON ds.dependent_artifact_id = ps.dependent_artifact_id
   AND ds.snapshot_at = ps.snapshot_at
  WHERE ps.next_seen_at IS NULL
    AND ds.next_snapshot_at IS NOT NULL
)

SELECT * FROM adds
UNION ALL
SELECT * FROM upgrades
UNION ALL
SELECT * FROM removals
