MODEL (
  name oso.stg_github__distinct_main_commits,
  description 'Gathers all github commits on the default branch of a repo that are distinct.',
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column created_at,
    batch_size 90,
    batch_concurrency 3,
    lookback 7
  ),
  start @github_incremental_start,
  partitioned_by DAY(created_at),
  dialect trino
);

@DEF(deduplication_window, 180);

/*
  Gathers all github commits on the default branch of a repo that are distinct.

  We use the `MIN_BY` method here to grab the first occurrence of a given commit
  in the case of duplicated event counts (which does seem to happen with some
  frequency). We only look back 180 days from the start date of the incremental
  query to avoid pulling in too much data to compare for the deduplication.

  This model uses a heuristic to determine the default branch of a repository.
  If the repository is not in the `stg_ossd__current_repositories` table, we
  assume the default branch is either `main` or `master`. If the repository is
  in the `stg_ossd__current_repositories` table, we use the branch specified
  there.
*/
SELECT
  ghc.repository_id,
  ghc.sha,
  MIN(ghc.created_at) AS created_at,
  ARG_MIN(ghc.repository_name, ghc.created_at) AS repository_name,
  ARG_MIN(ghc.push_id, ghc.created_at) AS push_id,
  ARG_MIN(ghc.ref, ghc.created_at) AS ref,
  ARG_MIN(ghc.actor_id, ghc.created_at) AS actor_id,
  ARG_MIN(ghc.actor_login, ghc.created_at) AS actor_login,
  ARG_MIN(ghc.author_email, ghc.created_at) AS author_email,
  ARG_MIN(ghc.author_name, ghc.created_at) AS author_name,
  ARG_MIN(ghc.is_distinct, ghc.created_at) AS is_distinct,
  ARG_MIN(ghc.api_url, ghc.created_at) AS api_url
FROM oso.stg_github__commits AS ghc
LEFT JOIN oso.stg_ossd__current_repositories AS repos
  ON ghc.repository_id = repos.id
WHERE ((repos.id IS NULL AND ghc.ref in ('refs/heads/main', 'refs/heads/master')) 
    OR (ghc.ref = CONCAT('refs/heads/', repos.branch)))
    AND ghc.created_at BETWEEN @start_dt - INTERVAL @deduplication_window DAY AND @end_dt
GROUP BY
  ghc.repository_id,
  ghc.sha