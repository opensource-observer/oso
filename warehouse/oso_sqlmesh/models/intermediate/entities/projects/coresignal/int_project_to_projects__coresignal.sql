MODEL (
  name oso.int_project_to_projects__coresignal,
  description 'Maps Coresignal companies to projects in OSS Directory',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH social AS (
  SELECT DISTINCT
    id AS coresignal_company_id,
    company_name AS coresignal_company_name,
    'TWITTER' AS artifact_source,
    TRIM(BOTH '"' FROM twitter_url_value::VARCHAR) AS artifact_url,
    REGEXP_EXTRACT(TRIM(BOTH '"' FROM twitter_url_value::VARCHAR), '(?:twitter|x)\\.com/([^/?#]+)', 1) AS artifact_owner
  FROM oso.stg_coresignal__companies
  CROSS JOIN UNNEST(twitter_urls) AS t(twitter_url_value)
  WHERE twitter_url_value IS NOT NULL
    AND REGEXP_EXTRACT(TRIM(BOTH '"' FROM twitter_url_value::VARCHAR), '(?:twitter|x)\\.com/([^/?#]+)', 1) IS NOT NULL

  UNION ALL

  SELECT DISTINCT
    id AS coresignal_company_id,
    company_name AS coresignal_company_name,
    'GITHUB' AS artifact_source,
    TRIM(BOTH '"' FROM github_url_value::VARCHAR) AS artifact_url,
    REGEXP_EXTRACT(TRIM(BOTH '"' FROM github_url_value::VARCHAR), 'github\\.com/([^/?#]+)', 1) AS artifact_owner
  FROM oso.stg_coresignal__companies
  CROSS JOIN UNNEST(github_urls) AS t(github_url_value)
  WHERE github_url_value IS NOT NULL
    AND REGEXP_EXTRACT(TRIM(BOTH '"' FROM github_url_value::VARCHAR), 'github\\.com/([^/?#]+)', 1) IS NOT NULL
),
abp AS (
   SELECT DISTINCT
     project_id AS oso_project_id,
     project_name AS oso_project_name,
     project_source AS oso_project_source,
     artifact_source,
     CASE
       WHEN artifact_source = 'GITHUB' THEN artifact_namespace
       ELSE artifact_name
     END AS artifact_owner
   FROM oso.artifacts_by_project_v1
   WHERE
     artifact_source IN ('GITHUB', 'TWITTER')
     AND project_source = 'OSS_DIRECTORY'
     AND project_namespace = 'oso'
),
project_matches AS (
  SELECT
    social.coresignal_company_id,
    social.coresignal_company_name,
    social.artifact_source,
    social.artifact_owner,
    social.artifact_url,
    abp.oso_project_id,
    abp.oso_project_name,
    abp.oso_project_source
  FROM social
  JOIN abp
  ON
    social.artifact_source = abp.artifact_source
    AND social.artifact_owner = abp.artifact_owner
),
-- Apply business logic to rank projects and identify best match
project_priority AS (
  SELECT
    coresignal_company_id,
    coresignal_company_name,
    artifact_source,
    artifact_owner,
    artifact_url,
    oso_project_id,
    oso_project_name,
    oso_project_source,
    -- Priority logic:
    -- 1. Projects with GITHUB artifacts get priority
    -- 2. Among projects with same artifact type, choose alphabetically by project name
    ROW_NUMBER() OVER (
      PARTITION BY coresignal_company_id 
      ORDER BY 
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
  artifact_url,
  oso_project_id,
  oso_project_name,
  oso_project_source
FROM project_priority
WHERE project_rank = 1