{#
  Daily active addresses to project by network
#}

SELECT
  e.project_id,
  e.from_namespace AS network,
  e.time,
  COUNT(
    DISTINCT CASE WHEN e.time = a.date_first_txn THEN e.from_id END
  ) AS new_addresses,
  COUNT(DISTINCT e.from_id) AS all_addresses
FROM {{ ref('int_events_to_project') }} AS e
LEFT JOIN {{ ref('int_addresses') }} AS a
  ON e.from_id = a.from_id
WHERE
  event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
GROUP BY 1, 2, 3
