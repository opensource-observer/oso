{#
  Many to many relationship table for collections
#}

SELECT 
  c.slug as `collection_slug`,
  project_slug
FROM {{ ref('stg_ossd__current_collections')}} AS c
CROSS JOIN UNNEST(c.projects) as project_slug