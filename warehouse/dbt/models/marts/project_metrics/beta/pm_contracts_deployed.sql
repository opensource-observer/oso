{#
  WIP: Still in Development
  Count the number of contracts deployed by a project
  that have more than 100 users
#}
{{ 
  config(meta = {
    'sync_to_cloudsql': False
  }) 
}}

{% set min_trusted_users = 100 %}

WITH users_by_contract AS (
  SELECT
    to_id AS artifact_id,
    COUNT(DISTINCT from_id) AS num_users
  FROM {{ ref('int_events_with_artifact_id') }}
  WHERE
    from_id IN (
      SELECT user_id
      FROM {{ ref('users') }}
      WHERE is_trusted = TRUE
    )
    AND event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
  GROUP BY 1
),

valid_contracts AS (
  SELECT artifact_id
  FROM users_by_contract
  WHERE num_users >= {{ min_trusted_users }}
)

SELECT
  a.project_id,
  COUNT(DISTINCT a.artifact_id) AS amount
FROM valid_contracts AS v
LEFT JOIN {{ ref('artifacts_by_project') }} AS a
  ON v.artifact_id = a.artifact_id
GROUP BY 1
