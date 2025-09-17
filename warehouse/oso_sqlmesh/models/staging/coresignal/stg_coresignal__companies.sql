MODEL (
  name oso.stg_coresignal__companies,
  description 'Companies data from Core Signal API',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH base_data AS (
  SELECT
    id::BIGINT AS id,
    company_name::VARCHAR AS company_name,
    website::VARCHAR AS website,
    crunchbase_url::VARCHAR AS crunchbase_url,
    CAST(JSON_EXTRACT(twitter_url, '$') AS ARRAY(VARCHAR)) AS twitter_urls,
    CAST(JSON_EXTRACT(github_url, '$') AS ARRAY(VARCHAR)) AS github_urls
  FROM @oso_source('bigquery_oso_dynamic.oso.coresignal_company_data')
)

SELECT DISTINCT
  id,
  company_name,
  'TWITTER'::VARCHAR AS url_type,
  TRIM(BOTH '"' FROM twitter_url_value::VARCHAR) AS url
FROM base_data
CROSS JOIN UNNEST(twitter_urls) AS t(twitter_url_value)
WHERE twitter_url_value IS NOT NULL

UNION ALL

SELECT DISTINCT
  id,
  company_name,
  'GITHUB'::VARCHAR AS url_type,
  TRIM(BOTH '"' FROM github_url_value::VARCHAR) AS url
FROM base_data
CROSS JOIN UNNEST(github_urls) AS t(github_url_value)
WHERE github_url_value IS NOT NULL

UNION ALL

SELECT DISTINCT
  id,
  company_name,
  'CRUNCHBASE'::VARCHAR AS url_type,
  TRIM(BOTH '"' FROM crunchbase_url::VARCHAR) AS url
FROM base_data
WHERE crunchbase_url IS NOT NULL

UNION ALL

SELECT DISTINCT
  id,
  company_name,
  'WEBSITE'::VARCHAR AS url_type,
  TRIM(BOTH '"' FROM website::VARCHAR) AS url
FROM base_data
WHERE website IS NOT NULL 