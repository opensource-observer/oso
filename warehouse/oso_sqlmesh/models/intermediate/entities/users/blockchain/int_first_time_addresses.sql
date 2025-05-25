model(
  name oso.int_first_time_addresses, 
  kind full, 
  enabled false,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

select *
from oso.stg_superchain__first_time_addresses
