{#
  Gathers all github commits on the default branch of a repo that are distinct.
#}

SELECT
  ghc.*
FROM {{ ref('stg_github__commits') }} as ghc
JOIN {{ ref('stg_ossd__current_repositories') }} as repos 
  ON ghc.repository_id = repos.id
WHERE ghc.ref = CONCAT("refs/heads/", repos.branch) AND ghc.is_distinct = TRUE
