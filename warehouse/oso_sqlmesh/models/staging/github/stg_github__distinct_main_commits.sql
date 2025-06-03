MODEL (
  name oso.stg_github__distinct_main_commits,
  description 'Gathers all github commits on the default branch of a repo that are distinct.',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column created_at,
    batch_size 90,
    batch_concurrency 3,
    lookback 31,
    forward_only true,
  ),
  start @github_incremental_start,
  partitioned_by DAY(created_at),
  dialect trino,
  audits (
    has_at_least_n_rows(threshold := 0),
    no_gaps(
      time_column := created_at,
      no_gap_date_part := 'day',
    ),
  )
);

@DEF(deduplication_window, 180);

/*
  Gathers all github commits on the default branch of a repo that are distinct.

  We use ROW_NUMBER() to grab the first occurrence of a given commit in the case of duplicated event counts (which does seem to happen with some frequency). We only look back 180 days from the start date of the incremental query to avoid pulling in too much data to compare for the deduplication.

  This model uses a heuristic to determine the default branch of a repository.
  If the repository is not in the `stg_ossd__current_repositories` table, we
  assume the default branch is either `main` or `master`. If the repository is
  in the `stg_ossd__current_repositories` table, we use the branch specified
  there.
*/
WITH deduped_commits AS (
  SELECT
    ghc.repository_id,
    ghc.sha,
    ghc.created_at,
    ghc.repository_name,
    ghc.push_id,
    ghc.ref,
    ghc.actor_id,
    ghc.actor_login,
    ghc.author_email,
    ghc.author_name,
    ghc.is_distinct,
    ghc.api_url,
    ROW_NUMBER() OVER (
      PARTITION BY ghc.repository_id, ghc.sha
      ORDER BY ghc.created_at ASC
    ) AS rn
  FROM oso.stg_github__commits AS ghc
  LEFT JOIN oso.stg_ossd__current_repositories AS repos
    ON ghc.repository_id = repos.id
  WHERE (
    (repos.id IS NULL AND ghc.ref IN ('refs/heads/main', 'refs/heads/master'))
    OR (ghc.ref = CONCAT('refs/heads/', repos.branch))
  )
    AND ghc.created_at BETWEEN @start_dt - INTERVAL @deduplication_window DAY AND @end_dt
)
SELECT
  repository_id,
  sha,
  created_at,
  repository_name,
  push_id,
  ref,
  actor_id,
  actor_login,
  author_email,
  author_name,
  is_distinct,
  api_url
FROM deduped_commits
WHERE rn = 1