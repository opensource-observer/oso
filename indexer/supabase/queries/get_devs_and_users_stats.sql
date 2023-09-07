WITH EventAggregation AS (
  SELECT
    e."contributorId",
    a.namespace,
    COUNT(*) AS event_count,
    MAX(e."eventTime") AS latest_event
  FROM
    "Event" e
    JOIN "Artifact" a ON e."artifactId" = a.id
  WHERE
    e."eventTime" >= current_timestamp - INTERVAL '30 days'
  GROUP BY
    e."contributorId",
    a.namespace
),
SharedContributors AS (
  SELECT
    e."contributorId",
    a.namespace,
    COUNT(DISTINCT p.id) AS project_count
  FROM
    "Event" e
    JOIN "Artifact" a ON e."artifactId" = a.id
    JOIN "ProjectsOnArtifacts" poa ON a.id = poa."artifactId"
    JOIN "Project" p ON poa."projectId" = p.id
  GROUP BY
    e."contributorId",
    a.namespace
  HAVING
    COUNT(DISTINCT p.id) > 1
)
SELECT
  p.name AS project_name,
  COUNT(DISTINCT CASE WHEN a.namespace = 'GITHUB' THEN e."contributorId" ELSE NULL END) AS unique_devs,
  COUNT(DISTINCT CASE WHEN a.namespace = 'GITHUB' AND ea.latest_event >= current_timestamp - INTERVAL '30 days' THEN ea."contributorId" ELSE NULL END) AS active_devs,
  COUNT(DISTINCT CASE WHEN a.namespace = 'GITHUB' AND ea.event_count >= 10 THEN ea."contributorId" ELSE NULL END) AS high_value_devs,
  
  COUNT(DISTINCT CASE WHEN a.namespace = 'OPTIMISM' THEN e."contributorId" ELSE NULL END) AS unique_users,
  COUNT(DISTINCT CASE WHEN a.namespace = 'OPTIMISM' AND ea.latest_event >= current_timestamp - INTERVAL '30 days' THEN ea."contributorId" ELSE NULL END) AS active_users,
  COUNT(DISTINCT CASE WHEN a.namespace = 'OPTIMISM' AND ea.event_count >= 10 THEN ea."contributorId" ELSE NULL END) AS high_value_users,

  COUNT(DISTINCT CASE WHEN a.namespace = 'GITHUB' AND sc."contributorId" IS NOT NULL THEN sc."contributorId" ELSE NULL END) AS shared_devs,
  COUNT(DISTINCT CASE WHEN a.namespace = 'OPTIMISM' AND sc."contributorId" IS NOT NULL THEN sc."contributorId" ELSE NULL END) AS shared_users
FROM
  "Project" p
  JOIN "ProjectsOnArtifacts" poa ON p.id = poa."projectId"
  JOIN "Artifact" a ON poa."artifactId" = a.id
  LEFT JOIN "Event" e ON a.id = e."artifactId"
  LEFT JOIN EventAggregation ea ON e."contributorId" = ea."contributorId" AND a.namespace = ea.namespace
  LEFT JOIN SharedContributors sc ON e."contributorId" = sc."contributorId" AND a.namespace = sc.namespace
WHERE
  p.name IN ('Uniswap', 'Safe', '0xSplits')
GROUP BY
  p.name
ORDER BY
  p.name;
