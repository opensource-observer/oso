{#
  Gathers all github commits on the default branch of a repo that are distinct.
#}
{{
  config(
    materialized='incremental'
  )
}}

SELECT
  ghc.*
FROM {{ ref('github_commits') }} as ghc
JOIN `oso-production.opensource_observer.repositories` as repos 
  ON ghc.repository_id = repos.id
WHERE ghc.ref = CONCAT("refs/heads/", repos.branch) AND ghc.is_distinct = TRUE
