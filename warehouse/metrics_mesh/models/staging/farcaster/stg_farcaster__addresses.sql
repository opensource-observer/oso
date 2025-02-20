MODEL (
  name metrics.stg_farcaster__addresses,
  description 'Get all verified addresses attached to an FID',
  dialect trino,
  kind FULL,
);

select
  cast(v.fid as string) as fid,
  lower(v.address) as address
from @oso_source('bigquery.farcaster.verifications') as v
where v.deleted_at is null
