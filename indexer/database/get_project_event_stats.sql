SELECT
    p."slug" AS project_slug,
    p."name" AS project_name,
    e."type" AS event_type,
    COUNT(e."id") AS total_events,
    COUNT(DISTINCT e."fromId") AS total_contributors,
    MIN(e."time") AS first_event_time,
    MAX(e."time") AS last_event_time
FROM
    project p
LEFT JOIN
    project_artifacts_artifact ON p."id" = project_artifacts_artifact."projectId"
LEFT JOIN
    artifact ON project_artifacts_artifact."artifactId" = artifact."id"
LEFT JOIN
    event e ON artifact."id" = e."toId"
LEFT JOIN
    collection_projects_project cpp ON p."id" = cpp."projectId"
LEFT JOIN
    collection c ON cpp."collectionId" = c."id"
WHERE
    e."type" IN (
        'PULL_REQUEST_CREATED',
        'PULL_REQUEST_MERGED',
        'COMMIT_CODE',
        'ISSUE_CLOSED',
        'PULL_REQUEST_CLOSED',
        'PULL_REQUEST_APPROVED',
        'ISSUE_CREATED',
        'STARRED',
        'FORKED'
    )
    AND e."time" IS NOT NULL
    --AND e."time" >= '2019-01-01'        
    AND c."slug" = 'ffdw-grants'    
GROUP BY
    p."slug",
    p."name",
    e."type"
ORDER BY
    project_name; 
