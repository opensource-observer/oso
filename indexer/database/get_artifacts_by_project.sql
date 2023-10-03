SELECT
    project."id" AS project_id,
    project."name" AS project_name,
    project."slug" AS project_slug,
    artifact."type" AS artifact_type,
    artifact."namespace" AS artifact_namespace,
    artifact."name" AS artifact_name
FROM
    project
LEFT JOIN
    project_artifacts_artifact ON project."id" = project_artifacts_artifact."projectId"
LEFT JOIN
    artifact ON project_artifacts_artifact."artifactId" = artifact."id";