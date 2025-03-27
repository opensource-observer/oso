CREATE SCHEMA IF NOT EXISTS bigquery.sqlmesh;

CREATE TABLE IF NOT EXISTS bigquery.sqlmesh.rendered_models (
    model_name varchar,
    rendered_sql varchar,
    rendered_at timestamp(6) with time zone,
    _dlt_load_id varchar,
    _dlt_id varchar
);

INSERT INTO
    bigquery.sqlmesh.rendered_models (
        model_name,
        rendered_sql,
        rendered_at,
        _dlt_load_id,
        _dlt_id
    )
VALUES
    (
        'stg_github__distinct_main_commits',
        'WITH "deduped_commits" AS (SELECT * FROM github_commits WHERE 1=1)',
        TIMESTAMP '2025-03-27 22:03:29.163110 UTC',
        '1743109399.194649',
        'aSe/ejttoOfiGA'
    ),
    (
        'int_all_artifacts',
        'WITH "onchain_artifacts" AS (SELECT * FROM deployers WHERE 1=1)',
        TIMESTAMP '2025-03-27 22:03:34.629756 UTC',
        '1743109399.194649',
        'OU72RpbQ0bJgAQ'
    ),
    (
        'int_contracts_transactions_weekly',
        'SELECT DATE_TRUNC(''WEEK'', "traces"."dt") AS "week" FROM traces WHERE 1=1',
        TIMESTAMP '2025-03-27 22:03:33.118413 UTC',
        '1743109399.194649',
        'z66vGMH5WnmO/g'
    ),
    (
        'int_derived_contracts_sort_weights',
        'SELECT UPPER("derived_contracts"."chain") FROM derived_contracts WHERE 1=1',
        TIMESTAMP '2025-03-27 22:03:32.967688 UTC',
        '1743109399.194649',
        'GY6hZ5Ir6NhESw'
    ),
    (
        'int_superchain_s7_onchain_metrics_by_project',
        'WITH "base_events" AS (SELECT * FROM events WHERE 1=1)',
        TIMESTAMP '2025-03-27 22:03:38.551416 UTC',
        '1743109399.194649',
        'WjrTD49+rmJhkA'
    );
