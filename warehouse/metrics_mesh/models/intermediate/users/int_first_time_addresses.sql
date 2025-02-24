MODEL (
  name metrics.int_first_time_addresses,
  kind FULL,
  enabled false,
);

select
  *
from metrics.stg_superchain__first_time_addresses
