
CREATE MATERIALIZED VIEW "EventsDailyByArtifact"
WITH (timescaledb.continuous) AS
SELECT "toArtifactId",
  "type",
   time_bucket(INTERVAL '1 day', "time") AS "bucketDaily",
   SUM(amount) as "amount"
FROM "EventTs" 
GROUP BY "toArtifactId", "type", "bucketDaily"
WITH NO DATA;

SELECT add_continuous_aggregate_policy('"EventsDailyByArtifact"',
  start_offset => INTERVAL '1 month',
  end_offset => INTERVAL '1 day',
  schedule_interval => INTERVAL '1 hour');

CREATE MATERIALIZED VIEW "EventsDailyByProject"
WITH (timescaledb.continuous) AS
SELECT "projectId",
  "type",
   time_bucket(INTERVAL '1 day', "time") AS "bucketDaily",
   SUM(amount) as "amount"
FROM "EventTs"
INNER JOIN "ProjectsOnArtifacts"
  on "ProjectsOnArtifacts"."artifactId" = "EventTs"."toArtifactId"
GROUP BY "projectId", "type", "bucketDaily"
WITH NO DATA;

SELECT add_continuous_aggregate_policy('"EventsDailyByProject"',
  start_offset => INTERVAL '1 month',
  end_offset => INTERVAL '1 day',
  schedule_interval => INTERVAL '1 hour');