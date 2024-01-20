{#
  Gathers all github events for all github artifacts
#}
{{
  config(
    materialized='incremental'
  )
}}

SELECT *
FROM {{ source('github_archive', 'events')}} as gh
JOIN  `oso-production.opensource_observer.repositories` as repos ON LOWER(gh.repo.name) = LOWER(repos.name)