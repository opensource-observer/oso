MODEL (
  name oso.int_project_to_projects__coresignal,
  description 'Maps Coresignal companies to projects in OSS Directory',
  dialect trino,
  kind FULL,
  audits (
    not_null(columns := (coresignal_company_id, oso_project_id))
  )
);

WITH social AS (
  SELECT DISTINCT
    id AS coresignal_company_id,
    company_name AS coresignal_company_name,
    url_type AS artifact_source,
    CASE 
      WHEN url_type = 'TWITTER' THEN REGEXP_EXTRACT(url, '(?:twitter|x)\\.com/([^/?#]+)', 1)
      WHEN url_type = 'GITHUB' THEN REGEXP_EXTRACT(url, 'github\\.com/([^/?#]+)', 1)
    END as artifact_owner,
    url as artifact_url
  FROM oso.stg_coresignal__companies
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
  oso_project_source,
  CASE WHEN project_rank = 1 THEN true ELSE false END AS is_best_match
FROM project_priority