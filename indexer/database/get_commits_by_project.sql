SELECT
    p."id" AS project_id,
    p."slug" as project_slug,
    p."name" AS project_name,
    e."type" AS event_type,
    a."name" AS artifact_name,
    e."fromId" AS contributor_id,
    e."time" AS event_time
FROM
    project p
LEFT JOIN
    project_artifacts_artifact pa ON p."id" = pa."projectId"
LEFT JOIN
    artifact a ON pa."artifactId" = a."id"
LEFT JOIN
    event e ON a."id" = e."toId"
LEFT JOIN
    collection_projects_project cpp ON p."id" = cpp."projectId"
LEFT JOIN
    collection c ON cpp."collectionId" = c."id"
WHERE
    e."type" = 'COMMIT_CODE'
    AND p."slug" = 'op';