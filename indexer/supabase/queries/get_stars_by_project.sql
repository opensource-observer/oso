-- This query counts incremental and cumulative stars by artifact (repo)

WITH StarredEvents AS (
    SELECT        
        a.name AS artifact_name,
        e."eventTime" AS event_time,
        TO_CHAR(e."eventTime", 'YYYY-MM') AS month
    FROM
        "Project" p
    JOIN
        "ProjectsOnArtifacts" poa ON p.id = poa."projectId"
    JOIN
        "Artifact" a ON poa."artifactId" = a.id
    LEFT JOIN
        "Event" e ON a.id = e."artifactId"
    WHERE
        e."eventType" = 'STARRED' AND 
        p.name = 'Uniswap' -- insert your project name here
)
SELECT
    artifact_name,    
    month,
    COUNT(*) AS star_count,
    CAST (SUM(COUNT(*)) OVER (PARTITION BY artifact_name ORDER BY month) AS integer) AS cumulative_stars
FROM
    StarredEvents
GROUP BY     
    artifact_name, month
ORDER BY
    artifact_name, month;
