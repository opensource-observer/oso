CREATE SCHEMA IF NOT EXISTS bigquery.defillama;

CREATE TABLE IF NOT EXISTS bigquery.defillama.tvl_events (
    time TIMESTAMP,
    slug VARCHAR,
    protocol VARCHAR,
    parent_protocol VARCHAR,
    chain VARCHAR,
    token VARCHAR,
    tvl DOUBLE,
    event_type VARCHAR,
    _dlt_load_id VARCHAR,
    _dlt_id VARCHAR
);

INSERT INTO bigquery.defillama.tvl_events (
    time,
    slug,
    protocol,
    parent_protocol,
    chain,
    token,
    tvl,
    event_type,
    _dlt_load_id,
    _dlt_id
)
VALUES
    (
        TIMESTAMP '2024-11-08 00:00:00.000000 UTC',
        'portal',
        'portal',
        '',
        'acala',
        'USD',
        0.0,
        'TVL',
        '1743009053.36983',
        'yflDrYc0mMETNg'
    ),
    (
        TIMESTAMP '2024-11-09 00:00:00.000000 UTC',
        'portal',
        'portal',
        '',
        'acala',
        'USD',
        0.0,
        'TVL',
        '1743009053.36983',
        'iy4nV9PKmMGEIg'
    ),
    (
        TIMESTAMP '2024-11-06 00:00:00.000000 UTC',
        'portal',
        'portal',
        '',
        'acala',
        'USD',
        121.31364,
        'TVL',
        '1743009053.36983',
        'ZiTAxzBJ+qexqQ'
    ),
    (
        TIMESTAMP '2024-11-04 00:00:00.000000 UTC',
        'portal',
        'portal',
        '',
        'acala',
        'USD',
        120.97663,
        'TVL',
        '1743009053.36983',
        'z7A8190d3UEznw'
    ),
    (
        TIMESTAMP '2024-11-03 00:00:00.000000 UTC',
        'portal',
        'portal',
        '',
        'acala',
        'USD',
        128.8515,
        'TVL',
        '1743009053.36983',
        'XBuflBJpHMq8bg'
    ),
    (
        TIMESTAMP '2024-11-06 00:00:00.000000 UTC',
        'portal',
        'portal',
        '',
        'algorand',
        'USD',
        50243.12289,
        'TVL',
        '1743009053.36983',
        'NdZiuWu9l7exQg'
    ),
    (
        TIMESTAMP '2024-11-03 00:00:00.000000 UTC',
        'portal',
        'portal',
        '',
        'algorand',
        'USD',
        94839.76255,
        'TVL',
        '1743009053.36983',
        'wDtpH0j4O8hQJA'
    ),
    (
        TIMESTAMP '2024-11-09 00:00:00.000000 UTC',
        'portal',
        'portal',
        '',
        'algorand',
        'USD',
        53368.60227,
        'TVL',
        '1743009053.36983',
        'HE6WvR82yX+ITg'
    );
