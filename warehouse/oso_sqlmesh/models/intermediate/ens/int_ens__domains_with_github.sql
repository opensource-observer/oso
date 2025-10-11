MODEL (
  name oso.int_ens__domains_with_github,
  description 'Intermediate model linking ENS domains to their GitHub handles extracted from text records',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH latest_github_handles AS (
  SELECT
    resolver,
    text_changed_value AS github_handle,
    ROW_NUMBER() OVER (
      PARTITION BY resolver
      ORDER BY block_number DESC, transaction_id DESC
    ) AS rn
  FROM oso.stg_ens__text_changeds
  WHERE text_changed_key = 'com.github'
    AND text_changed_value IS NOT NULL
    AND text_changed_value != ''
)

SELECT
  @oso_entity_id('ENS', '', d.name) AS domain_id,
  d.name AS domain_name,
  d.resolver AS resolver,
  gh.github_handle,
  @oso_entity_id('GITHUB', '', gh.github_handle) AS github_artifact_id
FROM oso.stg_ens__domains AS d
INNER JOIN latest_github_handles AS gh
  ON CAST(d.resolver->>'$.id' AS VARCHAR) = CAST(gh.resolver->>'$.id' AS VARCHAR)
WHERE gh.rn = 1
