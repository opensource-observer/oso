{#
  Gathers all github commits on the default branch of a repo that are distinct.

  We use the `MIN_BY` method here to grab the first occurrence of a given commit
  in the case of duplicated event counts (which does seem to happen with some
  frequency)
#}
SELECT
  MIN(ghc.created_at) AS created_at,
  ghc.repository_id,
  MIN_BY(ghc.repository_name, ghc.created_at) AS repository_name,
  MIN_BY(ghc.push_id, ghc.created_at) AS push_id,
  MIN_BY(ghc.ref, ghc.created_at) AS ref,
  MIN_BY(ghc.actor_id, ghc.created_at) AS actor_id,
  MIN_BY(ghc.actor_login, ghc.created_at) AS actor_login,
  ghc.sha,
  MIN_BY(ghc.author_email, ghc.created_at) AS author_email,
  MIN_BY(ghc.author_name, ghc.created_at) AS author_name,
  MIN_BY(ghc.is_distinct, ghc.created_at) AS is_distinct,
  MIN_BY(ghc.api_url, ghc.created_at) AS api_url
FROM {{ ref('stg_github__commits') }} as ghc
JOIN {{ ref('stg_ossd__current_repositories') }} as repos 
  ON ghc.repository_id = repos.id
WHERE ghc.ref = CONCAT("refs/heads/", repos.branch)

{# 
  We group by the repository id and sha to prevent merging commits between forks
  and in cases where duplicate shas exist between different repos
#}
GROUP BY ghc.repository_id, ghc.sha