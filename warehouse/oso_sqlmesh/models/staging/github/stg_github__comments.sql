MODEL (
  name oso.stg_github__comments,
  kind FULL
);

WITH pull_request_comment_events AS (
  SELECT
    ghe.id AS id,
    ghe.created_at AS event_time,
    ghe.repo.id AS repository_id,
    ghe.repo.name AS repository_name,
    ghe.actor.id AS actor_id,
    ghe.actor.login AS actor_login,
    'PULL_REQUEST_REVIEW_COMMENT' AS "type",
    CAST(ghe.payload -> '$.pull_request.number' AS BIGINT) AS "number",
    STRPTIME(ghe.payload ->> '$.pull_request.created_at', '%Y-%m-%dT%H:%M:%SZ') AS created_at,
    STRPTIME(ghe.payload ->> '$.pull_request.merged_at', '%Y-%m-%dT%H:%M:%SZ') AS merged_at,
    STRPTIME(ghe.payload ->> '$.pull_request.closed_at', '%Y-%m-%dT%H:%M:%SZ') AS closed_at,
    ghe.payload ->> '$.pull_request.state' AS "state",
    CAST(ghe.payload -> '$.pull_request.comments' AS DOUBLE) AS comments
  FROM oso.stg_github__events AS ghe
  WHERE
    ghe.type = 'PullRequestReviewCommentEvent'
), issue_comment_events AS (
  SELECT
    ghe.id AS id,
    ghe.created_at AS "event_time",
    ghe.repo.id AS repository_id,
    ghe.repo.name AS repository_name,
    ghe.actor.id AS actor_id,
    ghe.actor.login AS actor_login,
    'ISSUE_COMMENT' AS "type",
    CAST(ghe.payload -> '$.issue.number' AS INT) AS "number",
    STRPTIME(ghe.payload ->> '$.issue.created_at', '%Y-%m-%dT%H:%M:%SZ') AS created_at,
    NULL::TIMESTAMP AS merged_at,
    STRPTIME(ghe.payload ->> '$.issue.closed_at', '%Y-%m-%dT%H:%M:%SZ') AS closed_at,
    ghe.payload ->> '$.issue.state' AS "state",
    CAST(ghe.payload -> '$.issue.comments' AS DOUBLE) AS comments
  FROM oso.stg_github__events AS ghe
  WHERE
    ghe.type = 'IssueCommentEvent'
)
SELECT
  *
FROM pull_request_comment_events
UNION ALL
SELECT
  *
FROM issue_comment_events