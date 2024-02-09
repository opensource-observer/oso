WITH devs AS (
  SELECT
    p."id" AS "projectId",
    e."fromId" AS "fromId",
    time_bucket(INTERVAL '1 month', e."time") AS "bucketMonthly",
    CASE 
      WHEN COUNT(DISTINCT CASE WHEN t."name" = 'COMMIT_CODE' THEN e."time" END) >= 10 THEN 'FULL_TIME_DEV'
      WHEN COUNT(DISTINCT CASE WHEN t."name" = 'COMMIT_CODE' THEN e."time" END) >= 1 THEN 'PART_TIME_DEV'
      ELSE 'OTHER_CONTRIBUTOR'
    END AS "segmentType",
    1 AS amount
  FROM event e
  JOIN project_artifacts_artifact paa ON e."toId" = paa."artifactId"
  JOIN project p ON paa."projectId" = p.id        
  JOIN event_type t ON e."typeId" = t.id
  WHERE
  t."name" IN (
      'PULL_REQUEST_CREATED',
      'PULL_REQUEST_MERGED',
      'COMMIT_CODE',
      'ISSUE_CLOSED',
      'ISSUE_CREATED'
  )
  GROUP BY
    p."id",
    e."fromId",
    "bucketMonthly"
), users AS (
      SELECT 
          p."id" AS "projectId",
          e."fromId" AS "fromId",
          time_bucket(INTERVAL '1 month', e."time") AS "bucketMonthly",
          CASE 
              WHEN SUM(e."amount") >= 1000 THEN 'HIGH_FREQUENCY_USER'
              WHEN SUM(e."amount") >= 10 THEN 'HIGH_VALUE_USER'
              ELSE 'LOW_VALUE_USER'
          END AS "segmentType",
          1 AS amount
      FROM event e
      JOIN project_artifacts_artifact paa ON e."toId" = paa."artifactId"
      JOIN project p ON paa."projectId" = p.id
      JOIN event_type t ON e."typeId" = t.id
      WHERE t."name" = 'CONTRACT_INVOCATION_DAILY_COUNT'
      GROUP BY
        p."id",
        e."fromId",
        "bucketMonthly"
    )
    SELECT
      "projectId",
      "segmentType",
      "bucketMonthly",
      SUM("amount") AS "amount"
    FROM 
      (
          SELECT * FROM devs
          UNION ALL
          SELECT * FROM users
      ) combined_data
    GROUP BY
      "projectId",
      "segmentType",
      "bucketMonthly"