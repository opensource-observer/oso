model(
  name oso.int_first_time_addresses, 
  kind full, 
  enabled false,
  audits (
    number_of_rows(threshold := 0)
  )
);

select *
from oso.stg_superchain__first_time_addresses
