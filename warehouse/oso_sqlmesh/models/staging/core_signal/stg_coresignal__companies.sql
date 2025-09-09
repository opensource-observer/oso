MODEL (
  name oso.stg_core_signal__companies,
  description 'Companies data from Core Signal API',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  id::BIGINT AS id,
  company_name::VARCHAR AS name,
  website::VARCHAR AS website,
  crunchbase_url::VARCHAR AS crunchbase_url,
  CAST(JSON_EXTRACT(twitter_url, '$') AS ARRAY(VARCHAR)) AS twitter_url,
  CAST(JSON_EXTRACT(github_url, '$') AS ARRAY(VARCHAR)) AS github_url,
FROM @oso_source('bigquery_oso_dynamic.oso.coresignal_company_data') 