CREATE SCHEMA IF NOT EXISTS bigquery.lens_v2_polygon;

CREATE TABLE IF NOT EXISTS bigquery.lens_v2_polygon.profile_metadata (
    id bigint,
    profile_id varchar,
    name varchar,
    bio varchar,
    app varchar,
    metadata_json json,
    metadata_version varchar,
    metadata_uri varchar,
    metadata_snapshot_location_url varchar,
    profile_with_weights varchar,
    profile_picture_snapshot_location_url varchar,
    cover_picture_snapshot_location_url varchar,
    transaction_executor varchar,
    tx_hash varchar,
    block_hash varchar,
    block_number bigint,
    log_index bigint,
    tx_index bigint,
    block_timestamp timestamp(6) with time zone,
    datastream_metadata ROW(uuid varchar, source_timestamp bigint)
);

INSERT INTO
    bigquery.lens_v2_polygon.profile_metadata (
        id,
        profile_id,
        name,
        bio,
        app,
        metadata_json,
        metadata_version,
        metadata_uri,
        metadata_snapshot_location_url,
        profile_with_weights,
        profile_picture_snapshot_location_url,
        cover_picture_snapshot_location_url,
        transaction_executor,
        tx_hash,
        block_hash,
        block_number,
        log_index,
        tx_index,
        block_timestamp,
        datastream_metadata
    )
VALUES
    (
        1,
        'profile_1',
        'Alice',
        'Bio 1',
        'App 1',
        json_parse(
            '{"$schema":"https://json-schemas.lens.dev/profile/2.0.0.json","lens":{"id":"bde8f4d9-34a3-4d27-b98c-0b871f857dcd","name":"Alice"}}'
        ),
        'v1',
        'uri_1',
        'snapshot_url_1',
        'weights_1',
        'picture_url_1',
        'cover_url_1',
        'executor_1',
        'tx_hash_1',
        'block_hash_1',
        1001,
        1,
        1,
        current_timestamp - interval '2' day,
        ROW('uuid_1', 1234567890)
    ),
    (
        2,
        'profile_2',
        'Bob',
        'Bio 2',
        'App 2',
        json_parse(
            '{"$schema":"https://json-schemas.lens.dev/profile/2.0.0.json","lens":{"id":"fcdd6027-b5de-4584-9ec5-557fc93ef7e6","name":"Bob"}}'
        ),
        'v2',
        'uri_2',
        'snapshot_url_2',
        'weights_2',
        'picture_url_2',
        'cover_url_2',
        'executor_2',
        'tx_hash_2',
        'block_hash_2',
        1002,
        2,
        2,
        current_timestamp - interval '1' day,
        ROW('uuid_2', 1234567891)
    );

CREATE TABLE IF NOT EXISTS bigquery.lens_v2_polygon.profile_ownership_history (
    history_id bigint,
    profile_id varchar,
    owned_by varchar,
    tx_hash varchar,
    block_hash varchar,
    block_number bigint,
    log_index bigint,
    tx_index bigint,
    block_timestamp timestamp(6) with time zone,
    datastream_metadata ROW(uuid varchar, source_timestamp bigint)
);

INSERT INTO
    bigquery.lens_v2_polygon.profile_ownership_history (
        history_id,
        profile_id,
        owned_by,
        tx_hash,
        block_hash,
        block_number,
        log_index,
        tx_index,
        block_timestamp,
        datastream_metadata
    )
VALUES
    (
        1,
        'profile_1',
        'owner_1',
        'tx_hash_1',
        'block_hash_1',
        1001,
        1,
        1,
        current_timestamp - interval '2' day,
        ROW('uuid_1', 1234567890)
    ),
    (
        2,
        'profile_2',
        'owner_2',
        'tx_hash_2',
        'block_hash_2',
        1002,
        2,
        2,
        current_timestamp - interval '1' day,
        ROW('uuid_2', 1234567891)
    );