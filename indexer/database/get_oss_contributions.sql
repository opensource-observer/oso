SELECT
    project."id" AS project_id,
    project."name" AS project_name,
    event."fromId" AS contributor_id,
    event."type" AS event_type,
    event."time" AS event_time,
    artifact."name" AS artifact_name
FROM
    project
LEFT JOIN
    project_artifacts_artifact ON project."id" = project_artifacts_artifact."projectId"
LEFT JOIN
    artifact ON project_artifacts_artifact."artifactId" = artifact."id"
LEFT JOIN
    event ON artifact."id" = event."toId"
WHERE
    artifact."namespace" = 'GITHUB'
    AND event."fromId" IS NOT NULL
ORDER BY
    event."fromId";
