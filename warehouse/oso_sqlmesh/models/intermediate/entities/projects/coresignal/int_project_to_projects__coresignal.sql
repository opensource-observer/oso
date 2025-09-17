MODEL (
  name oso.int_project_to_projects__coresignal,
  description 'Maps Coresignal companies to projects in OSS Directory',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

@DEF(twitter_regex, '(?:twitter|x)\.com/([^/?#]+)');
@DEF(github_regex, 'github\.com/([^/?#]+)');

WITH social AS (
  SELECT DISTINCT
    id AS coresignal_company_id,
    company_name AS coresignal_company_name,
    'TWITTER' AS artifact_source,
    TRIM(BOTH '"' FROM twitter_url_value) AS artifact_url,
    REGEXP_EXTRACT(TRIM(BOTH '"' FROM twitter_url_value), @twitter_regex, 1) AS artifact_owner
  FROM oso.stg_coresignal__companies
  CROSS JOIN UNNEST(twitter_urls) AS t(twitter_url_value)
  WHERE twitter_url_value IS NOT NULL
    AND REGEXP_EXTRACT(TRIM(BOTH '"' FROM twitter_url_value), @twitter_regex, 1) IS NOT NULL

  UNION ALL

  SELECT DISTINCT
    id AS coresignal_company_id,
    company_name AS coresignal_company_name,
    'GITHUB' AS artifact_source,
    TRIM(BOTH '"' FROM github_url_value) AS artifact_url,
    REGEXP_EXTRACT(TRIM(BOTH '"' FROM github_url_value), @github_regex, 1) AS artifact_owner
  FROM oso.stg_coresignal__companies
  CROSS JOIN UNNEST(github_urls) AS t(github_url_value)
  WHERE github_url_value IS NOT NULL
    AND REGEXP_EXTRACT(TRIM(BOTH '"' FROM github_url_value), @github_regex, 1) IS NOT NULL
),
abp AS (
   SELECT
     project_id AS oso_project_id,
     project_name AS oso_project_name,
     project_source AS oso_project_source,
     artifact_source,
     CASE
       WHEN artifact_source = 'GITHUB' THEN artifact_namespace
       ELSE artifact_name
     END AS artifact_owner,
     COUNT(DISTINCT artifact_id) AS num_artifacts
   FROM oso.artifacts_by_project_v1
   WHERE
     artifact_source IN ('GITHUB', 'TWITTER')
     AND project_source = 'OSS_DIRECTORY'
     AND project_namespace = 'oso'
  GROUP BY 1,2,3,4,5
),
project_matches AS (
  SELECT
    social.coresignal_company_id,
    social.coresignal_company_name,
    social.artifact_source,
    social.artifact_owner,
    abp.oso_project_id,
    abp.oso_project_name,
    abp.oso_project_source,
    abp.num_artifacts
  FROM social
  JOIN abp
  ON
    social.artifact_source = abp.artifact_source
    AND social.artifact_owner = abp.artifact_owner
  WHERE social.artifact_owner NOT IN ('ethereum')
),
-- Apply business logic to rank projects and identify best match
project_priority AS (
  SELECT
    coresignal_company_id,
    coresignal_company_name,
    artifact_source,
    artifact_owner,
    oso_project_id,
    oso_project_name,
    oso_project_source,
    -- Priority logic:
    -- 1. Projects with more shared artifacts get priority
    -- 2. Projects with GITHUB artifacts get priority
    -- 3. Tie breaker: choose alphabetically by project name
    ROW_NUMBER() OVER (
      PARTITION BY coresignal_company_id 
      ORDER BY 
        num_artifacts DESC,
        CASE WHEN artifact_source = 'GITHUB' THEN 1 ELSE 2 END,
        oso_project_name ASC
    ) AS project_rank
  FROM project_matches
)

SELECT DISTINCT
  coresignal_company_id,
  coresignal_company_name,
  artifact_source,
  artifact_owner,
  oso_project_id,
  oso_project_name,
  oso_project_source,
  (project_rank=1) AS is_best_match
FROM project_priority