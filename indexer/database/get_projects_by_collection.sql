SELECT 
    project.id,
    project.slug,
    project.name 
FROM 
    project
LEFT JOIN
    collection_projects_project on project.id = collection_projects_project."projectId"
LEFT JOIN
    collection on collection_projects_project."collectionId" = collection.id
WHERE
    collection.slug = 'optimism';