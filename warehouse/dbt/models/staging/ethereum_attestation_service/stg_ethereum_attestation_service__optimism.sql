select
  id,
  attester,
  recipient,
  ref_uid,
  schema_id,
  decoded_data_json,
  revocable,
  revoked,
  is_offchain,
  txid as transaction_hash,
  timestamp_seconds(`time`) as `time`,
  case
    when expiration_time != 0 then timestamp_seconds(expiration_time)
  end as expiration_time,
  case
    when revocation_time != 0 then timestamp_seconds(revocation_time)
  end as revocation_time
from {{ source("ethereum_attestation_service_optimism", "attestations") }}
