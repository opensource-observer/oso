WITH EventData AS (
    SELECT
        p."slug" AS project_slug,
        p."name" AS project_name,
        e."id" AS event_id,
        e."fromId" AS contributor_id,
        TO_CHAR(e."time", 'YYYY-MM') AS month_year
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
        e."type" = 'COMMIT_CODE'
        AND e."time" IS NOT NULL
        --AND e."time" >= '2017-01-01'        
        AND c."slug" = 'ffdw-grants'    
)
SELECT
    project_slug,
    project_name,
    month_year,
    COUNT(event_id) AS total_commits,
    COUNT(DISTINCT contributor_id) AS total_contributors
FROM
    EventData
GROUP BY
    project_slug,
    project_name,
    month_year
ORDER BY
    project_slug; 
