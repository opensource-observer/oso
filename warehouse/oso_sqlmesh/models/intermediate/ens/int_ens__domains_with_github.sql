MODEL (
  name oso.int_ens__domains_with_github,
  description 'Intermediate model for ENS domains with GitHub handles extracted from text records',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  d.id AS domain_id,
  d.name AS domain_name,
  tc.value AS github_handle
FROM oso.stg_ens__domains AS d
INNER JOIN oso.stg_ens__text_changeds AS tc
  ON CAST(d.resolver->>'$.id' AS VARCHAR) = CAST(tc.resolver->>'$.id' AS VARCHAR)
WHERE tc.key = 'com.github'
