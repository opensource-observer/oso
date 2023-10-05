WITH EventData AS (
    SELECT
        p."slug" AS project_slug,
        p."name" AS project_name,
        e."id" AS event_id,
        e."fromId" AS contributor_id,
        TO_CHAR(e."time", 'YYYY-MM') AS month_year
    FROM
        project p
    JOIN
        project_artifacts_artifact paa ON p."id" = paa."projectId"
    JOIN
        artifact a ON paa."artifactId" = a."id"
    JOIN
        event e ON a."id" = e."toId"
    JOIN
        collection_projects_project cpp ON p."id" = cpp."projectId"
    JOIN
        collection c ON cpp."collectionId" = c."id"
    JOIN (
        SELECT
            a."id" AS artifact_id,
            MIN(e."time") AS first_star_time
        FROM
            artifact a
        LEFT JOIN
            event e ON a."id" = e."toId" AND e."type" = 'STARRED'
        WHERE
            e."time" IS NOT NULL
        GROUP BY
            a."id"
    ) fse ON a."id" = fse.artifact_id
    WHERE
        e."time" >= %s
        AND e."type" IN (
            'COMMIT_CODE',
            'PULL_REQUEST_CREATED',
            'PULL_REQUEST_MERGED',
            'PULL_REQUEST_CLOSED',
            'PULL_REQUEST_APPROVED',
            'ISSUE_CLOSED',
            'ISSUE_CREATED'
        )
        AND c."slug" = %s
        AND e."time" > fse.first_star_time -- Filter events after the first star event
)
, ContributorEventCounts AS (
    SELECT
        project_slug,
        month_year,
        contributor_id
    FROM (
        SELECT
            project_slug,
            month_year,
            contributor_id,
            COUNT(*) AS event_count
        FROM
            EventData
        GROUP BY
            project_slug,
            month_year,
            contributor_id
    ) subquery
    WHERE event_count >= 10
)
SELECT
    ed.project_slug,
    ed.project_name,
    ed.month_year,
    COUNT(DISTINCT ed.contributor_id) AS total_contributors,
    COUNT(DISTINCT cec.contributor_id) AS contributors_with_more_than_10_events
FROM
    EventData ed
LEFT JOIN
    ContributorEventCounts cec
ON
    ed.project_slug = cec.project_slug
    AND ed.month_year = cec.month_year
GROUP BY
    ed.project_slug,
    ed.project_name,
    ed.month_year
ORDER BY
    ed.project_slug;