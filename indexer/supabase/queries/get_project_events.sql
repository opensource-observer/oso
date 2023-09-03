-- This query retrieves all events associated with a specific project.
SELECT
    p.id AS project_id,
    p.name AS project_name,
    a.namespace as artifact_namespace,
    a.name AS artifact_name,
    c.name AS contributor_name,
    e."eventType" AS event_type,
    e."eventTime" AS event_time
FROM
    "Project" p
JOIN
    "ProjectsOnArtifacts" poa ON p.id = poa."projectId"
JOIN
    "Artifact" a ON poa."artifactId" = a.id
LEFT JOIN
    "Event" e ON a.id = e."artifactId"
LEFT JOIN
    "Contributor" c ON e."contributorId" = c.id
WHERE
    p.name = 'Uniswap'; -- insert your project name here