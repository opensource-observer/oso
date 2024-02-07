{#
  Many to many relationship table for collections
#}

SELECT 
  c.slug as `collection_slug`,
  p as `project_slug`,
FROM `oso-production.opensource_observer.collections` AS c
CROSS JOIN UNNEST(c.projects) as p