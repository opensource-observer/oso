MODEL (
  name oso.stg_ens__domains_with_github,
  description 'ENS domains with GitHub handles extracted from text records',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
  enabled false
);

SELECT
  d.id AS domain_id,
  d.name AS domain_name,
  tc.value AS github_handle
FROM @oso_source('bigquery.ens.domains') AS d
INNER JOIN @oso_source('bigquery.ens.text_changeds') AS tc
  ON CAST(d.resolver->>'$.id' AS VARCHAR) = CAST(tc.resolver->>'$.id' AS VARCHAR)
WHERE tc.key = 'com.github';
