MODEL (
  name oso.stg_ens__domains,
  description 'Staging model for ENS domains - preserves all source fields without unnesting',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

SELECT
  id,
  name,
  resolver,
  owner,
  registrant,
  expiry_date,
  registration,
  subdomains,
  subdomain_count
FROM @oso_source('bigquery.ens.domains_tmp')
