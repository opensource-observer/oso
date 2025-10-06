MODEL (
  name oso.stg_coresignal__companies,
  description 'Companies data from Core Signal API - one row per company',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0),
    not_null(columns := (id, company_name))
  )
);

SELECT
  id::BIGINT AS id,
  company_name::VARCHAR AS company_name,
  website::VARCHAR AS website,
  crunchbase_url::VARCHAR AS crunchbase_url,
  CAST(JSON_EXTRACT(twitter_url, '$') AS ARRAY(VARCHAR)) AS twitter_urls,
  CAST(JSON_EXTRACT(github_url, '$') AS ARRAY(VARCHAR)) AS github_urls
FROM @oso_source('bigquery_oso_dynamic.oso.coresignal_company_data')
WHERE id IS NOT NULL 
  AND company_name IS NOT NULL 