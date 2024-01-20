WITH
  all_repos AS (
  SELECT
    projects.slug as project_slug,
    'GITHUB' AS namespace,
    'REPOSITORY' AS type,
    LOWER(repos.name) AS name,
    LOWER(repos.url) AS url
  FROM
    `oso-production.opensource_observer.projects` AS projects
  CROSS JOIN
    UNNEST(JSON_EXTRACT_ARRAY(projects.github)) AS github
  JOIN
    `oso-production.opensource_observer.repositories` AS repos
  ON
    LOWER(repos.owner) = LOWER(JSON_EXTRACT_SCALAR(github.url))
    OR LOWER(repos.url) = LOWER(JSON_EXTRACT_SCALAR(github.url))
  GROUP BY
    1,
    2,
    3,
    4,
    5 ),
  all_npm AS (
  SELECT
    projects.slug,
    'NPM' AS namespace,
    'PACKAGE' AS type,
    CASE
      WHEN LOWER(JSON_EXTRACT_SCALAR(npm.url)) LIKE 'https://npmjs.com/package/%' THEN SUBSTR(LOWER(JSON_EXTRACT_SCALAR(npm.url)), 28)
      WHEN LOWER(JSON_EXTRACT_SCALAR(npm.url)) LIKE 'https://www.npmjs.com/package/%' THEN SUBSTR(LOWER(JSON_EXTRACT_SCALAR(npm.url)), 31)
    END AS name,
    LOWER(JSON_EXTRACT_SCALAR(npm.url)) AS url
  FROM
    `oso-production.opensource_observer.projects` AS projects
  CROSS JOIN
    UNNEST(JSON_EXTRACT_ARRAY(projects.npm)) AS npm ),
  all_blockchain AS (
  SELECT
    projects.slug,
    UPPER(network) AS namespace,
    UPPER(tag) AS type,
    JSON_EXTRACT_SCALAR(blockchains.address) AS name,
    JSON_EXTRACT_SCALAR(blockchains.address) AS url
  FROM
    `oso-production.opensource_observer.projects` AS projects
  CROSS JOIN
    UNNEST(JSON_EXTRACT_ARRAY(projects.blockchain)) AS blockchains
  CROSS JOIN
    UNNEST(JSON_EXTRACT_STRING_ARRAY(blockchains.networks)) AS network
  CROSS JOIN
    UNNEST(JSON_EXTRACT_STRING_ARRAY(blockchains.tags)) AS tag 
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
  select * from all_artifacts group by 1,2,3,4,5
)
SELECT * FROM all_unique_artifacts