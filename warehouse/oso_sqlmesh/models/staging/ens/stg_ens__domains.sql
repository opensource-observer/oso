MODEL (
  name oso.stg_ens__domains,
  description 'Staging model for ENS domains - preserves all source fields without unnesting',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  ),
);

SELECT
  id,
  name,
  TRY_CAST(resolver AS ROW(id VARCHAR)) AS resolver,
  TRY_CAST(owner AS ROW(id VARCHAR)) AS owner,
  TRY_CAST(registrant AS ROW(id VARCHAR)) AS registrant,
  expiry_date,
  TRY_CAST(registration AS ROW(id VARCHAR)) AS registration,
  TRY_CAST(subdomains AS ARRAY(VARCHAR)) AS subdomains,
  subdomain_count
FROM @oso_source('bigquery.ens.domains_tmp')
