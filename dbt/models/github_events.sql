{#
  Gathers all github events for all github artifacts
#}
{{
  config(
    materialized='incremental'
  )
}}

SELECT gh.*
FROM {{ source('github_archive', 'events')}} as gh
JOIN `oso-production.opensource_observer.repositories` as repos ON gh.repo.id = repos.id