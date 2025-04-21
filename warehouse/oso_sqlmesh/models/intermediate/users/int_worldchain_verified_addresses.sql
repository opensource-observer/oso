MODEL (
  name oso.int_worldchain_verified_addresses,
  kind FULL,
  description "Worldchain verified addresses",
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH users AS (
  SELECT
    verified_address,
    MIN(block_timestamp) AS first_verified_at,
    MAX(address_verified_until) AS verified_until
  FROM oso.stg_worldchain__verified_users
  GROUP BY 1
)

SELECT
  @oso_entity_id('WORLDCHAIN', '', users.verified_address) AS user_id,
  users.verified_address,
  users.first_verified_at,
  users.verified_until
FROM users
