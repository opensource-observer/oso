WITH EventsData AS (
    SELECT
        e."id" as event_id,
        p."slug" as project_slug,
        e."fromId" AS contributor_id,
        TO_CHAR(e."time", 'YYYY-MM') AS month_year,
        e."type" AS event_type
    FROM
        project p
    LEFT JOIN
        project_artifacts_artifact pa ON p."id" = pa."projectId"
    LEFT JOIN
        artifact a ON pa."artifactId" = a."id"
    LEFT JOIN
        event e ON a."id" = e."toId"
    LEFT JOIN
        collection_projects_project cpp ON p."id" = cpp."projectId"
    LEFT JOIN
        collection c ON cpp."collectionId" = c."id"
    WHERE
        e."time" IS NOT NULL
        AND e."time" >= '2019-01-01'        
        AND c."slug" = 'optimism'
),
Contributors AS (
    SELECT
        project_slug,
        contributor_id,
        month_year,
        COUNT(event_id) AS total_commits,
        CASE
            WHEN COUNT(event_id) >= 10 THEN 'full-time'
            WHEN COUNT(event_id) >= 1 THEN 'part-time'
            ELSE 'no-commit'
        END AS contributor_type
    FROM
        EventsData
    WHERE
        event_type = 'COMMIT_CODE'
    GROUP BY
        project_slug,
        month_year,
        contributor_id
),
ContributorData AS (
    SELECT
        project_slug,
        month_year,
        SUM(CASE WHEN contributor_type = 'full-time' THEN 1 ELSE 0 END) AS full_time_developers,
        SUM(CASE WHEN contributor_type = 'part-time' THEN 1 ELSE 0 END) AS part_time_developers,
        SUM(total_commits) AS total_commits
    FROM
        Contributors
    GROUP BY
        project_slug,
        month_year
),
StarsData AS (
    SELECT
        project_slug,
        month_year,
        COALESCE(COUNT(event_id), 0) AS stars
    FROM
        EventsData
    WHERE
        event_type = 'STARRED'
    GROUP BY
        project_slug,
        month_year
)

SELECT
    cd.project_slug,
    cd.month_year,
    SUM(cd.full_time_developers) AS full_time_developers,
    SUM(cd.part_time_developers) AS part_time_developers,
    SUM(cd.total_commits) AS total_commits,
    SUM(sd.stars) AS stars
FROM
    ContributorData cd
LEFT JOIN
    StarsData sd ON cd.project_slug = sd.project_slug AND cd.month_year = sd.month_year
GROUP BY
    cd.project_slug, cd.month_year
ORDER BY
    cd.project_slug, cd.month_year;

