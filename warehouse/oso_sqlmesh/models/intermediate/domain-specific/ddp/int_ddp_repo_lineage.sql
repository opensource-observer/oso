MODEL (
  name oso.int_ddp_repo_lineage,
  description "Lineage for DDP repos: one row per (artifact_id, artifact_source_id) from the registry, plus canonical/alias state for migrations",
  kind FULL,
  dialect trino,
  grain (artifact_id, artifact_source_id),
  tags (
    'entity_category=artifact'
  ),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH ddp_repos AS (
  SELECT
    artifact_id,
    artifact_namespace,
    artifact_name
  FROM oso.int_ddp_repo_metadata
),

repo_commits AS (
  SELECT
    artifact_id,
    artifact_namespace,
    artifact_name,
    artifact_source_id,
    first_commit_time,
    last_commit_time
  FROM oso.int_first_last_commit_to_github_repository
),

-- DDP artifacts with their observed source-IDs and windows
registered_ranges AS (
  SELECT
    r.artifact_id,
    r.artifact_namespace,
    r.artifact_name,
    r.artifact_source_id,
    r.first_commit_time,
    r.last_commit_time
  FROM repo_commits AS r
  WHERE r.artifact_id IN (
    SELECT artifact_id FROM ddp_repos
  )
),

-- All rows (DDP + non-DDP) that share any source-id with a DDP artifact
alias_ranges AS (
  SELECT
    a.artifact_id,
    a.artifact_namespace,
    a.artifact_name,
    a.artifact_source_id,
    a.first_commit_time,
    a.last_commit_time
  FROM repo_commits AS a
  WHERE a.artifact_source_id IN (
    SELECT DISTINCT artifact_source_id FROM registered_ranges
  )
),

-- Resolve the earliest and latest source-id per DDP artifact
first_last_source_id AS (
  SELECT
    artifact_id,
    MIN_BY(artifact_source_id, first_commit_time) AS first_artifact_source_id,
    MAX_BY(artifact_source_id, last_commit_time) AS last_artifact_source_id
  FROM registered_ranges
  GROUP BY artifact_id
),

-- Map a source-id to the earliest and latest artifact_id it belonged to
-- (across the full universe of repos that ever had that source-id)
source_to_first_last_artifact AS (
  SELECT
    artifact_source_id,
    MIN_BY(artifact_id, first_commit_time) AS first_artifact_id,
    MAX_BY(artifact_id, last_commit_time) AS last_artifact_id
  FROM alias_ranges
  GROUP BY artifact_source_id
),

-- Pick a single, representative namespace/name per artifact_id (latest seen)
artifact_profile AS (
  SELECT
    artifact_id,
    MAX_BY(artifact_namespace, last_commit_time) AS artifact_namespace,
    MAX_BY(artifact_name, last_commit_time) AS artifact_name
  FROM alias_ranges
  GROUP BY artifact_id
),

-- Family = all artifact_ids that have ever shared any source-id with the DDP artifact
family_links AS (
  SELECT
    rr.artifact_id AS ddp_artifact_id,
    ar.artifact_id AS related_artifact_id
  FROM registered_ranges AS rr
  JOIN alias_ranges AS ar
    ON ar.artifact_source_id = rr.artifact_source_id
),

family_agg AS (
  SELECT
    ddp_artifact_id AS artifact_id,
    ARRAY_SORT(
      ARRAY_DISTINCT(
        ARRAY_AGG(related_artifact_id)
      )
    ) AS family_artifact_ids
  FROM family_links
  GROUP BY ddp_artifact_id
),

-- Denormalized “first/last artifact_id” per DDP artifact
ddp_first_last AS (
  SELECT
    fls.artifact_id AS artifact_id,
    sff.first_artifact_id AS first_artifact_id,
    sfl.last_artifact_id AS last_artifact_id
  FROM first_last_source_id AS fls
  JOIN source_to_first_last_artifact AS sff
    ON sff.artifact_source_id = fls.first_artifact_source_id
  JOIN source_to_first_last_artifact AS sfl
    ON sfl.artifact_source_id = fls.last_artifact_source_id
),

-- Roll profiles for first/last artifact_ids
ddp_first_last_labeled AS (
  SELECT
    dfl.artifact_id AS artifact_id,
    dfl.first_artifact_id AS first_artifact_id,
    ap1.artifact_namespace  AS first_artifact_namespace,
    ap1.artifact_name AS first_artifact_name,
    dfl.last_artifact_id AS last_artifact_id,
    ap2.artifact_namespace AS last_artifact_namespace,
    ap2.artifact_name AS last_artifact_name
  FROM ddp_first_last AS dfl
  LEFT JOIN artifact_profile AS ap1
    ON ap1.artifact_id = dfl.first_artifact_id
  LEFT JOIN artifact_profile AS ap2
    ON ap2.artifact_id = dfl.last_artifact_id
),

-- Convenience aggregates for booleans and counts
ddp_flags AS (
  SELECT
    r.artifact_id AS artifact_id,
    CASE
      WHEN r.artifact_id = dfl.last_artifact_id THEN true
      ELSE false
    END AS is_current_url,
    CARDINALITY(
      FILTER(
        fa.family_artifact_ids,
        x -> x <> r.artifact_id
      )
    ) AS alias_count,
    CASE
      WHEN CARDINALITY(
             FILTER(fa.family_artifact_ids, x -> x <> r.artifact_id)
           ) > 0
      THEN true
      ELSE false
    END AS has_aliases
  FROM registered_ranges AS r
  LEFT JOIN family_agg AS fa
    ON fa.artifact_id = r.artifact_id
  LEFT JOIN ddp_first_last AS dfl
    ON dfl.artifact_id = r.artifact_id
),

deduped AS (
  SELECT DISTINCT
    r.artifact_id,
    r.artifact_namespace,
    r.artifact_name,
    dfl.first_artifact_id,
    dfl.first_artifact_namespace,
    dfl.first_artifact_name,
    dfl.last_artifact_id,
    dfl.last_artifact_namespace,
    dfl.last_artifact_name,
    df.is_current_url,
    df.has_aliases,
    df.alias_count
  FROM ddp_repos AS r
  LEFT JOIN ddp_first_last_labeled AS dfl
    ON dfl.artifact_id = r.artifact_id
  LEFT JOIN ddp_flags AS df
    ON df.artifact_id = r.artifact_id  
)

SELECT
  d.artifact_id,
  d.artifact_namespace,
  d.artifact_name,
  d.first_artifact_id,
  d.first_artifact_namespace,
  d.first_artifact_name,
  d.last_artifact_id,
  d.last_artifact_namespace,
  d.last_artifact_name,
  d.is_current_url,
  d.has_aliases,
  d.alias_count,
  fa.family_artifact_ids
FROM deduped AS d
LEFT JOIN family_agg AS fa
  ON fa.artifact_id = d.artifact_id