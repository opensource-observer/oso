-- This query identifies active blockchain users of a project
WITH UserInteractions AS (
    SELECT
        e."contributorId" AS contributor_id,
        COUNT(*) AS interaction_count
    FROM
        "Event" e
    JOIN
        "Artifact" a ON e."artifactId" = a.id
    JOIN
        "ProjectsOnArtifacts" poa ON a.id = poa."artifactId"
    JOIN
        "Project" p ON poa."projectId" = p.id
    WHERE
        e."eventTime" >= CURRENT_DATE - INTERVAL '30 days' AND
        e."eventTime" < CURRENT_DATE AND
        e."eventType" = 'CONTRACT_INVOKED' AND
        p.name = 'Uniswap' -- insert your project name here
    GROUP BY
        e."contributorId"
)
SELECT
    c.id AS contributor_id,
    c.name AS contributor_name,
    ui.interaction_count
FROM
    "Contributor" c
JOIN
    UserInteractions ui ON c.id = ui.contributor_id
ORDER BY 3 DESC;