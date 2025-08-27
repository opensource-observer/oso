MODEL (
  name oso.stg_ens__domains_with_github,
  description 'ENS domains with GitHub handles extracted from text records',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  tags (
    "staging"
  )
);

SELECT
  domains.id AS domain_id,
  domains.name AS domain_name,
  text_changeds.value AS github_handle
FROM @oso_source('bigquery.ens.domains') AS domains
INNER JOIN @oso_source('bigquery.ens.text_changeds') AS text_changeds
  ON JSON_EXTRACT_SCALAR(text_changeds.resolver, '$.id') = JSON_EXTRACT_SCALAR(domains.resolver, '$.id')
WHERE text_changeds.key = 'com.github'
  AND text_changeds.value IS NOT NULL
  AND text_changeds.value != ''
