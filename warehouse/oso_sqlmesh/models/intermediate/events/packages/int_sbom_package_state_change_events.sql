MODEL (
  name oso.int_sbom_package_state_change_events,
  description 'Events tracking the lifecycle of dependencies (add, upgrade, remove) based on SBOM snapshots',
  kind FULL,
  dialect trino,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH base_raw AS (
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
      dependent_artifact_id,
      package_artifact_id,
      snapshot_at,
      package_version,
      @semver_extract(package_version, 'major') AS major,
      @semver_extract(package_version, 'minor') AS minor,
      @semver_extract(package_version, 'patch') AS patch,
      ROW_NUMBER() OVER(
        PARTITION BY dependent_artifact_id, package_artifact_id, snapshot_at
        ORDER BY
          @semver_extract(package_version, 'major') DESC,
          @semver_extract(package_version, 'minor') DESC,
          @semver_extract(package_version, 'patch') DESC,
          package_version DESC
      ) AS rn
    FROM oso.int_sbom_from_ossd
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
presence AS (
  SELECT DISTINCT
    dependent_artifact_id,
    package_artifact_id,
    package_version,
    snapshot_at,
    major,
    minor,
    patch
  FROM monthly_base
),
presence_seq AS (
  SELECT
    p.*,
    ROW_NUMBER() OVER(PARTITION BY dependent_artifact_id, package_artifact_id ORDER BY snapshot_at) AS rn,
    LAG(package_version) OVER(PARTITION BY dependent_artifact_id, package_artifact_id ORDER BY snapshot_at) AS prev_version,
    LAG(major) OVER(PARTITION BY dependent_artifact_id, package_artifact_id ORDER BY snapshot_at) AS prev_major,
    LAG(minor) OVER(PARTITION BY dependent_artifact_id, package_artifact_id ORDER BY snapshot_at) AS prev_minor,
    LAG(patch) OVER(PARTITION BY dependent_artifact_id, package_artifact_id ORDER BY snapshot_at) AS prev_patch
  FROM presence AS p
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
last_presence AS (
  SELECT
    dependent_artifact_id,
    package_artifact_id,
    MAX(snapshot_at) AS last_seen_at,
    MAX_BY(package_version, snapshot_at) AS last_version
  FROM presence
  GROUP BY 1, 2
),
removals AS (
  SELECT
    'REMOVE_DEPENDENCY' AS event_type,
    ds.next_snapshot_at AS event_time,
    lp.dependent_artifact_id,
    lp.package_artifact_id,
    lp.last_version AS version_before,
    CAST(NULL AS varchar) AS version_after
  FROM last_presence AS lp
  JOIN dependent_snapshots_seq AS ds
    ON ds.dependent_artifact_id=lp.dependent_artifact_id
   AND ds.snapshot_at=lp.last_seen_at
  WHERE ds.next_snapshot_at IS NOT NULL
),
events_union AS (
  SELECT * FROM adds
  UNION ALL
  SELECT * FROM upgrades
  UNION ALL
  SELECT * FROM removals
),
enriched AS (
  SELECT
    e.*,
    ROW_NUMBER() OVER(
      PARTITION BY e.dependent_artifact_id, e.package_artifact_id, e.event_time
      ORDER BY b.snapshot_at DESC
    ) AS rn
  FROM events_union AS e
  LEFT JOIN monthly_base AS b
    ON b.dependent_artifact_id = e.dependent_artifact_id
   AND b.package_artifact_id = e.package_artifact_id
   AND b.snapshot_at <= e.event_time
)
SELECT
  event_type,
  event_time,
  dependent_artifact_id,
  package_artifact_id,
  version_before,
  version_after
FROM enriched
WHERE rn=1 OR rn IS NULL
