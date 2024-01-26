WITH
  all_repos AS (
  SELECT
    projects.slug as project_slug,
    'GITHUB' AS namespace,
    'REPOSITORY' AS type,
    LOWER(repos.name) AS name,
    LOWER(repos.url) AS url,
    repos.node_id AS source_id
  FROM
    `oso-production.opensource_observer.projects` AS projects
  CROSS JOIN
    UNNEST(JSON_QUERY_ARRAY(projects.github)) AS github
  JOIN
    `oso-production.opensource_observer.repositories` AS repos
  ON
    LOWER(repos.owner) = LOWER(JSON_VALUE(github.url))
    OR LOWER(repos.url) = LOWER(JSON_VALUE(github.url))
  GROUP BY
    1,
    2,
    3,
    4,
    5, 
    6 ),
  all_npm AS (
  SELECT
    projects.slug,
    'NPM' AS namespace,
    'PACKAGE' AS type,
    CASE
      WHEN LOWER(JSON_VALUE(npm.url)) LIKE 'https://npmjs.com/package/%' THEN SUBSTR(LOWER(JSON_VALUE(npm.url)), 28)
      WHEN LOWER(JSON_VALUE(npm.url)) LIKE 'https://www.npmjs.com/package/%' THEN SUBSTR(LOWER(JSON_VALUE(npm.url)), 31)
    END AS name,
    LOWER(JSON_VALUE(npm.url)) AS url,
    LOWER(JSON_VALUE(npm.url)) AS source_id,
  FROM
    `oso-production.opensource_observer.projects` AS projects
  CROSS JOIN
    UNNEST(JSON_QUERY_ARRAY(projects.npm)) AS npm ),
  all_blockchain AS (
  SELECT
    projects.slug,
    UPPER(network) AS namespace,
    UPPER(tag) AS type,
    JSON_VALUE(blockchains.address) AS name,
    JSON_VALUE(blockchains.address) AS url,
    JSON_VALUE(blockchains.address) AS source_id
  FROM
    `oso-production.opensource_observer.projects` AS projects
  CROSS JOIN
    UNNEST(JSON_QUERY_ARRAY(projects.blockchain)) AS blockchains
  CROSS JOIN
    UNNEST(JSON_VALUE_ARRAY(blockchains.networks)) AS network
  CROSS JOIN
    UNNEST(JSON_VALUE_ARRAY(blockchains.tags)) AS tag 
), all_artifacts AS (
SELECT
  *
FROM
  all_repos
UNION ALL
SELECT
  *
FROM
  all_blockchain
UNION ALL
SELECT
  *
FROM
  all_npm
), all_unique_artifacts AS (
  select * from all_artifacts group by 1,2,3,4,5,6
)
SELECT * FROM all_unique_artifacts