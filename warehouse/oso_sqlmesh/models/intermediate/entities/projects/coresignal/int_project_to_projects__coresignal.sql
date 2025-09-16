MODEL (
  name oso.int_project_to_projects__coresignal,
  description 'Maps Coresignal companies to OSO projects',
  dialect trino,
  kind FULL,
  audits (
    not_null(columns := (id, oso_project_id))
  )
);

WITH social AS (
  SELECT DISTINCT
    @oso_entity_id('CORESIGNAL', '', CAST(id AS VARCHAR)) AS id,
    id as source_id,
    name,
    url_type as artifact_source,
    CASE 
      WHEN url_type = 'TWITTER' THEN REGEXP_EXTRACT(url, '(?:twitter|x)\\.com/([^/?#]+)', 1)
      WHEN url_type = 'GITHUB' THEN REGEXP_EXTRACT(url, 'github\\.com/([^/?#]+)', 1)
    END as artifact_owner,
    url as artifact_url
  FROM oso.stg_coresignal__companies
),
abp AS (
   SELECT DISTINCT
     project_id,
     project_name,
     project_source,
     artifact_source,
     CASE
       WHEN artifact_source = 'GITHUB' THEN artifact_namespace
       ELSE artifact_name
     END AS artifact_owner
   FROM oso.artifacts_by_project_v1
   WHERE
     artifact_source IN ('GITHUB', 'TWITTER')
     AND project_source IN ('OSS_DIRECTORY', 'CRYPTO_ECOSYSTEMS')
     AND project_namespace IN ('oso', 'eco')
)

SELECT
  social.*,
  abp.project_id as oso_project_id,
  abp.project_name as oso_project_name,
  abp.project_source as oso_project_source
FROM social
LEFT JOIN abp
ON
  social.artifact_source = abp.artifact_source
  AND social.artifact_owner = abp.artifact_owner