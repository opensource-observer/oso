MODEL (
  name oso.stg_github__distinct_main_commits,
  description 'Gathers all github commits on the default branch of a repo that are distinct.',
  kind FULL
);

/*
  Gathers all github commits on the default branch of a repo that are distinct.

  We use the `MIN_BY` method here to grab the first occurrence of a given commit
  in the case of duplicated event counts (which does seem to happen with some
  frequency)
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
INNER JOIN oso.stg_ossd__current_repositories AS repos
  ON ghc.repository_id = repos.id
WHERE
  ghc.ref = CONCAT('refs/heads/', repos.branch)
GROUP BY
  ghc.repository_id,
  ghc.sha