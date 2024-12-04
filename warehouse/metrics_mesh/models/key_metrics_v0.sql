MODEL (
  name metrics.key_metrics_v0,
  kind FULL,
  dialect "clickhouse"
);

-- for type in ['artifact', 'project', 'collection']:
--   render_query(
--     ref='key_metrics_v0.sql',
--     config={ macros: { 'id': f'{type}_id', 'to_id': f'to_{type}_id' } }
--   ) # generates `metrics.key_metrics_v0_by_{type}`

-- another approach: get all metrics from oso_metrics (metrics_factories)
-- filter out those we do not care about
-- transform each to the structure we want (id, amount, metric, ..) (sql cte?, macro?)
-- plug into this model
-- generate `metrics.key_metrics_v0_by_{type}` à la timeseries
-- with `metrics_start` and `metrics_end` as `start epoch` and `end` as `@now()`
-- create three models like timeseries does to expose the three types

-- TODO(jabolo): change to artifact/project/collection dynamically
@DEF(id, artifact_id);
@DEF(to_id, to_artifact_id);

-- TODO(jabolo): Remove this, it is just for reference of some local playground events
@DEF(all_events, [
  'ISSUE_REOPENED',
  'PULL_REQUEST_REOPENED',
  'ISSUE_CLOSED',
  'ISSUE_COMMENT',
  'FORKED',
  'CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT',
  'CONTRACT_INVOCATION_DAILY_L2_GAS_USED',
  'PULL_REQUEST_OPENED',
  'PULL_REQUEST_MERGED',
  'COMMIT_CODE',
  'DEBIT',
  'STARRED',
  'CREDIT',
  'PULL_REQUEST_REVIEW_COMMENT',
  'RELEASE_PUBLISHED',
  'ISSUE_OPENED',
  'ADD_DEPENDENCY',
  'CONTRACT_INVOCATION_DAILY_COUNT',
  'PULL_REQUEST_CLOSED',
]);

WITH all_events AS (
  SELECT * 
  FROM metrics.events_daily_to_artifact
),

total_commits AS (
  SELECT
    @to_id AS @id,
    COUNT(*) AS amount,
    'TOTAL_COMMITS' AS metric,
    'COUNT' AS unit
  FROM all_events
  WHERE event_type = 'COMMIT_CODE'
  GROUP BY @to_id
),

first_commit AS (
  SELECT
    @to_id AS @id,
    @str_to_unix_timestamp(
      CAST(MIN(bucket_day) AS STRING)
    ) AS amount,
    'FIRST_COMMIT' AS metric,
    'DATE' AS unit
  FROM all_events
  WHERE event_type = 'COMMIT_CODE'
  GROUP BY @to_id
),

last_commit AS (
  SELECT
    @to_id AS @id,
    @str_to_unix_timestamp(
      CAST(MAX(bucket_day) AS STRING)
    ) AS amount,
    'LAST_COMMIT' AS metric,
    'DATE' AS unit
  FROM all_events
  WHERE event_type = 'COMMIT_CODE'
  GROUP BY @to_id
),

star_count AS (
  SELECT
    @to_id AS @id,
    COUNT(*) AS amount,
    'STAR_COUNT' AS metric,
    'COUNT' AS unit
  FROM all_events
  WHERE event_type = 'STARRED'
  GROUP BY @to_id
),

fork_count AS (
  SELECT
    @to_id AS @id,
    COUNT(*) AS amount,
    'FORK_COUNT' AS metric,
    'COUNT' AS unit
  FROM all_events
  WHERE event_type = 'FORKED'
  GROUP BY @to_id
),

developer_count AS (
  SELECT
    @to_id AS @id,
    COUNT(DISTINCT from_artifact_id) AS amount,
    'DEVELOPER_COUNT' AS metric,
    'COUNT' AS unit
  FROM all_events
  WHERE event_type IN ('COMMIT_CODE', 'PULL_REQUEST_OPENED')
  GROUP BY @to_id
),

commit_count AS (
  SELECT
    @to_id AS @id,
    COUNT(*) AS amount,
    'COMMIT_COUNT' AS metric,
    'COUNT' AS unit
  FROM all_events
  WHERE event_type = 'COMMIT_CODE'
  GROUP BY @to_id
),

opened_pull_request_count AS (
  SELECT
    @to_id AS @id,
    COUNT(*) AS amount,
    'OPENED_PULL_REQUEST_COUNT' AS metric,
    'COUNT' AS unit
  FROM all_events
  WHERE event_type = 'PULL_REQUEST_OPENED'
  GROUP BY @to_id
),

merged_pull_request_count AS (
  SELECT
    @to_id AS @id,
    COUNT(*) AS amount,
    'MERGED_PULL_REQUEST_COUNT' AS metric,
    'COUNT' AS unit
  FROM all_events
  WHERE event_type = 'PULL_REQUEST_MERGED'
  GROUP BY @to_id
),

opened_issue_count AS (
  SELECT
    @to_id AS @id,
    COUNT(*) AS amount,
    'OPENED_ISSUE_COUNT' AS metric,
    'COUNT' AS unit
  FROM all_events
  WHERE event_type = 'ISSUE_OPENED'
  GROUP BY @to_id
),

closed_issue_count AS (
  SELECT
    @to_id AS @id,
    COUNT(*) AS amount,
    'CLOSED_ISSUE_COUNT' AS metric,
    'COUNT' AS unit
  FROM all_events
  WHERE event_type = 'ISSUE_CLOSED'
  GROUP BY @to_id
),

comment_count AS (
  SELECT
    @to_id AS @id,
    COUNT(*) AS amount,
    'COMMENT_COUNT' AS metric,
    'COUNT' AS unit
  FROM all_events
  WHERE event_type = 'ISSUE_COMMENT'
  GROUP BY @to_id
),

release_count AS (
  SELECT
    @to_id AS @id,
    COUNT(*) AS amount,
    'RELEASE_COUNT' AS metric,
    'COUNT' AS unit
  FROM all_events
  WHERE event_type = 'RELEASE_PUBLISHED'
  GROUP BY @to_id
),

transaction_count AS (
  SELECT
    @to_id AS @id,
    COUNT(*) AS amount,
    'TRANSACTION_COUNT' AS metric,
    'COUNT' AS unit
  FROM all_events
  WHERE event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
  GROUP BY @to_id
),

all_key_metrics AS (
  @OSO_UNION(
    'CTE',
    'ALL',
    total_commits,
    first_commit,
    last_commit,
    star_count,
    fork_count,
    developer_count,
    commit_count,
    opened_pull_request_count,
    merged_pull_request_count,
    opened_issue_count,
    closed_issue_count,
    comment_count,
    release_count,
    transaction_count
  )
)

SELECT 
  @oso_id('OSO', 'oso', metric) AS metric_id,
  metric::STRING AS _debug_metric,
  @id::STRING,
  amount::FLOAT64,
  unit::STRING,
  NOW()::DATE AS snapshot_at,
FROM all_key_metrics
