-- This query counts incremental and cumulative commits by contributor
-- includes a simple bot filter

WITH FilteredData AS (
    SELECT
        p.name AS project_name,
        c.name AS contributor_name,
        e."eventType" AS event_type,
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
    LEFT JOIN
        "Contributor" c ON e."contributorId" = c.id
    WHERE
        p.name = 'Uniswap' -- insert your project name here
        AND e."eventType" = 'COMMIT_CODE' -- insert GitHub event type here
)
SELECT
    contributor_name,
    month,
    COUNT(event_time) AS commits,
    CAST(SUM(COUNT(*)) OVER (PARTITION BY contributor_name ORDER BY month) AS integer) AS cumulative_commits,
    CASE WHEN 
      contributor_name LIKE '%-bot%' 
      OR contributor_name = 'web-flow'
    THEN True ELSE False END AS is_bot
FROM
    FilteredData
GROUP BY
    contributor_name,
    month
ORDER BY
    contributor_name, month DESC;
