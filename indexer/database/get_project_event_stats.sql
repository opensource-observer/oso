SELECT
    project."name" AS project_name,
    event."type" AS event_type,
    COUNT(event."id") AS total_events,
    COUNT(DISTINCT event."fromId") AS total_contributors,
    MIN(event."time") AS first_event_time,
    MAX(event."time") AS last_event_time
FROM
    project
LEFT JOIN
    project_artifacts_artifact ON project."id" = project_artifacts_artifact."projectId"
LEFT JOIN
    artifact ON project_artifacts_artifact."artifactId" = artifact."id"
LEFT JOIN
    event ON artifact."id" = event."toId"
GROUP BY
    project."name",
    event."type"
ORDER BY
    total_events DESC;
