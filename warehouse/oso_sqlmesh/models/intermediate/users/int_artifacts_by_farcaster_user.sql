MODEL (
  name oso.int_artifacts_by_farcaster_user,
  kind FULL,
  description "EVM addresses linked to Farcaster IDs"
);

WITH farcaster_addresses AS (
  SELECT DISTINCT
    farcaster_id,
    address
  FROM oso.stg_farcaster__addresses
  WHERE LENGTH(address) = 42
),

custody_addresses AS (
  SELECT DISTINCT
    farcaster_id,
    custody_address AS address
  FROM oso.stg_farcaster__profiles
  WHERE custody_address IS NOT NULL
),

all_addresses AS (
  SELECT *
  FROM farcaster_addresses
  UNION ALL
  SELECT *
  FROM custody_addresses
)

SELECT
  @oso_entity_id('FARCASTER', '', profiles.farcaster_id) AS user_id,
  profiles.farcaster_id,
  profiles.username AS farcaster_username,
  all_addresses.address
FROM all_addresses
JOIN oso.stg_farcaster__profiles AS profiles
  ON all_addresses.farcaster_id = profiles.farcaster_id
