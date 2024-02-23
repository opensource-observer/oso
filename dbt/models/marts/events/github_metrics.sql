{# 
  Summary GitHub metrics for a project:
    - First commit date
    - Total repositories
    - Total stars
    - Total forks
    - Total contributors
    - Total contributors in the last 6 months
    - Average active developers over the last 6 months
    - Total commits over the last 6 months
    - Total issues opened over the last 6 months
    - Total issues closed over the last 6 months
    - Total pull requests opened over the last 6 months
    - Total pull requests merged over the last 6 months
#}

-- CTE for aggregating stars, forks, and repository counts by project 
WITH StarsForksRepos AS (
    SELECT
        project_id,
        -- Count of distinct repositories associated with the project
        COUNT(DISTINCT id) AS repos,
        -- Sum of stars for the project
        SUM(star_count) AS stars,
        -- Sum of forks for the project
        SUM(fork_count) AS forks
    FROM {{ ref('stg_ossd__repositories_by_project') }}
    WHERE is_fork = false
    GROUP BY project_id
),
-- CTE for calculating contributor counts, including active developers over the past 6 months
Contributors AS (
    SELECT
        project_id,
        -- Total distinct contributors for the project
        COUNT(DISTINCT from_id) AS contributors,
        -- Contributors active within the last 6 months
        COUNT(DISTINCT
            CASE 
                WHEN DATE(bucket_month) >= DATE_ADD(CURRENT_DATE(), INTERVAL -180 DAY) THEN from_id 
            END
        ) AS contributors_6_months,
        -- Average number of active developers (full-time or part-time) per month over the last 6 months
        COUNT(DISTINCT
            CASE 
                WHEN DATE(bucket_month) >= DATE_ADD(CURRENT_DATE(), INTERVAL -180 DAY) 
                     AND user_segment_type IN ('FULL_TIME_DEV', 'PART_TIME_DEV') THEN from_id 
            END
        ) / 6 AS avg_active_devs_6_months
    FROM {{ ref('int_devs') }}
    GROUP BY project_id
),
-- CTE for summarizing project activity metrics over the past 6 months
Activity AS (
    SELECT
        project_id,
        MIN(CASE WHEN event_type = 'COMMIT_CODE' THEN time END) AS first_commit_date,
        SUM(CASE WHEN event_type = 'COMMIT_CODE' THEN amount END) AS commits,
        SUM(CASE WHEN event_type = 'ISSUE_OPENED' THEN amount END) AS issues_opened,
        SUM(CASE WHEN event_type = 'ISSUE_CLOSED' THEN amount END) AS issues_closed,
        SUM(CASE WHEN event_type = 'PULL_REQUEST_OPENED' THEN amount END) AS pull_requests_opened,
        SUM(CASE WHEN event_type = 'PULL_REQUEST_MERGED' THEN amount END) AS pull_requests_merged
    FROM {{ ref('int_events_to_project') }}
    WHERE DATE(time) >= DATE_ADD(CURRENT_DATE(), INTERVAL -180 DAY)
    GROUP BY project_id
)

-- Final query to join all the metrics together
SELECT
    p.project_id,
    p.project_name,
    act.first_commit_date,    
    sfr.repos,
    sfr.stars,
    sfr.forks,
    c.contributors,
    c.contributors_6_months,
    c.avg_active_devs_6_months,
    act.commits,
    act.issues_opened,
    act.issues_closed,
    act.pull_requests_opened,
    act.pull_requests_merged
    
FROM {{ ref('projects') }} AS p
JOIN StarsForksRepos AS sfr ON p.project_id = sfr.project_id
JOIN Contributors AS c ON p.project_id = c.project_id
JOIN Activity AS act ON p.project_id = act.project_id