{{
  config(
    materialized='table',
  ) if target.name in ['playground', 'dev'] else config(
    enabled=false,
  )
}}
SELECT * 
FROM {{ source('ossd', 'projects') }}