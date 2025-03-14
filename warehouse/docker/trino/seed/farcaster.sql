CREATE SCHEMA IF NOT EXISTS bigquery.farcaster;

CREATE TABLE IF NOT EXISTS bigquery.farcaster.profiles (
   fid bigint NOT NULL,
   last_updated_at timestamp(6) with time zone,
   data json,
   custody_address varchar
);

INSERT INTO
   bigquery.farcaster.profiles (fid, last_updated_at, data, custody_address)
VALUES
   (
      1,
      current_timestamp - interval '2' day,
      json_parse('{"username": "Alice"}'),
      '0x123'
   ),
   (
      2,
      current_timestamp - interval '1' day,
      json_parse('{"username": "Bob"}'),
      '0x456'
   );

CREATE TABLE IF NOT EXISTS bigquery.farcaster.verifications (
   fid bigint NOT NULL,
   address varchar NOT NULL,
   timestamp timestamp(6) with time zone NOT NULL,
   deleted_at timestamp(6) with time zone
);

INSERT INTO
   bigquery.farcaster.verifications (fid, address, timestamp, deleted_at)
VALUES
   (
      1,
      '0x123',
      current_timestamp - interval '2' day,
      NULL
   ),
   (
      2,
      '0x456',
      current_timestamp - interval '1' day,
      NULL
   );