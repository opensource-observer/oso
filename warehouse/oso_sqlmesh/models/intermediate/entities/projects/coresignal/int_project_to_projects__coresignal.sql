MODEL (
  name oso.int_project_to_projects__coresignal,
  description 'Maps Coresignal companies to projects in OSS Directory',
  dialect trino,
  kind FULL,
  audits (
    not_null(columns := (id, oso_project_id))
  )
);

WITH social AS (
  SELECT DISTINCT
    id AS coresignal_company_id,
    name AS coresignal_company_name,
    url_type AS artifact_type,
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
)

SELECT
  social.coresignal_company_id,
  social.coresignal_company_name,
  social.artifact_type,
  social.artifact_owner,
  social.artifact_url,
  abp.oso_project_id,
  abp.oso_project_name,
  abp.oso_project_source
FROM social
LEFT JOIN abp
ON
  social.artifact_source = abp.artifact_source
  AND social.artifact_owner = abp.artifact_owner