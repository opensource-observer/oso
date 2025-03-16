MODEL (
  name oso.int_artifacts,
  description 'All artifacts',
  kind FULL
);

WITH all_artifacts AS (
  /*
    This grabs all the artifacts we know about from project sources
    and from the contract discovery process.
  */
  SELECT
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_url,
    artifact_name
  FROM oso.int_artifacts_by_project
  UNION ALL
  /*
    This grabs the universe of blockchain artifacts that have interacted with the contracts we care about from the events table.
    TODO: this should be refactored when we "index the universe"
  */
  SELECT DISTINCT
    artifact_source_id,
    artifact_source,
    LOWER(artifact_source) AS artifact_namespace,
    artifact_source_id AS artifact_name,
    artifact_source_id AS artifact_url
  FROM (
    SELECT
      from_artifact_source_id AS artifact_source_id,
      event_source AS artifact_source
    FROM @oso_source('bigquery.oso.int_events__blockchain')
    WHERE
      event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
    UNION ALL
    SELECT
      to_artifact_source_id AS artifact_source_id,
      event_source AS artifact_source
    FROM @oso_source('bigquery.oso.int_events__blockchain')
    WHERE
      event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
  )
  UNION ALL
  /* 
    This grabs the universe of GitHub users that have interacted with the repos we care about.
    The `last_used` value is later used in this query to determine what the most _current_ name is. However, oss-directory names are considered canonical so `last_used` is only relevent for `git_user` artifacts.
  */
  SELECT
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_url,
    ARG_MAX(artifact_name, last_used) AS artifact_name
  FROM oso.int_artifacts_history
  GROUP BY
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_url
)
SELECT DISTINCT
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name) AS artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url
FROM all_artifacts
