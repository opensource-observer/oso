MODEL (
  name oso.int_ossd_interface,
  description "Interface model for OSS Directory data that transforms source-specific schema to standard schema",
  kind FULL,
  dialect trino,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

/*
  This interface model abstracts the details of the OSS Directory staging models
  and transforms them into a standardized schema that can be consumed by the
  int_raw_artifacts model.
  
  Benefits:
  - Isolates source-specific logic
  - Makes it easier to handle changes in source data
  - Provides a clear contract between staging and intermediate layers
*/

WITH projects AS (
  SELECT
    project_id,
    websites,
    social,
    github,
    npm,
    blockchain,
    defillama,
    updated_at
  FROM oso.stg_ossd__current_projects
), 

-- Website artifacts
website_artifacts AS (
  SELECT
    projects.project_id,
    unnested_website.url AS artifact_source_id,
    'WWW' AS artifact_source,
    '' AS artifact_namespace,
    unnested_website.url AS artifact_name,
    unnested_website.url AS artifact_url,
    'WEBSITE' AS artifact_type,
    projects.updated_at AS last_updated_at
  FROM projects
  CROSS JOIN UNNEST(projects.websites) AS @unnested_struct_ref(unnested_website)
), 

-- Social media artifacts
farcaster_artifacts AS (
  SELECT
    projects.project_id,
    unnested_farcaster.url AS artifact_source_id,
    'FARCASTER' AS artifact_source,
    '' AS artifact_namespace,
    CASE
      WHEN unnested_farcaster.url LIKE 'https://warpcast.com/%'
      THEN SUBSTRING(unnested_farcaster.url, 22)
      ELSE unnested_farcaster.url
    END AS artifact_name,
    unnested_farcaster.url AS artifact_url,
    'SOCIAL_HANDLE' AS artifact_type,
    projects.updated_at AS last_updated_at
  FROM projects
  CROSS JOIN UNNEST(projects.social.farcaster) AS @unnested_struct_ref(unnested_farcaster)
), 

twitter_artifacts AS (
  SELECT
    projects.project_id,
    unnested_twitter.url AS artifact_source_id,
    'TWITTER' AS artifact_source,
    '' AS artifact_namespace,
    CASE
      WHEN unnested_twitter.url LIKE 'https://twitter.com/%'
      THEN SUBSTRING(unnested_twitter.url, 21)
      WHEN unnested_twitter.url LIKE 'https://x.com/%'
      THEN SUBSTRING(unnested_twitter.url, 15)
      ELSE unnested_twitter.url
    END AS artifact_name,
    unnested_twitter.url AS artifact_url,
    'SOCIAL_HANDLE' AS artifact_type,
    projects.updated_at AS last_updated_at
  FROM projects
  CROSS JOIN UNNEST(projects.social.twitter) AS @unnested_struct_ref(unnested_twitter)
), 

-- GitHub repositories
github_artifacts AS (
  SELECT
    projects.project_id,
    repos.id::VARCHAR AS artifact_source_id,
    'GITHUB' AS artifact_source,
    repos.owner AS artifact_namespace,
    repos.name AS artifact_name,
    LOWER(CONCAT('https://github.com/', repos.owner, '/', repos.name)) AS artifact_url,
    'REPOSITORY' AS artifact_type,
    projects.updated_at AS last_updated_at
  FROM projects
  CROSS JOIN UNNEST(projects.github) AS @unnested_struct_ref(unnested_github)
  INNER JOIN oso.stg_ossd__current_repositories AS repos
    ON LOWER(CONCAT('https://github.com/', repos.owner)) = LOWER(TRIM(TRAILING '/' FROM unnested_github.url))
    OR LOWER(repos.url) = LOWER(TRIM(TRAILING '/' FROM unnested_github.url))
), 

-- NPM packages
npm_artifacts AS (
  SELECT
    projects.project_id,
    unnested_npm.url AS artifact_source_id,
    'NPM' AS artifact_source,
    SPLIT(REPLACE(
      CASE
        WHEN unnested_npm.url LIKE 'https://npmjs.com/package/%'
        THEN SUBSTRING(unnested_npm.url, 27)
        WHEN unnested_npm.url LIKE 'https://www.npmjs.com/package/%'
        THEN SUBSTRING(unnested_npm.url, 31)
        ELSE unnested_npm.url
      END, 
      '@', ''
    ), '/')[@array_index(0)] AS artifact_namespace,
    CASE
      WHEN unnested_npm.url LIKE 'https://npmjs.com/package/%'
      THEN SUBSTRING(unnested_npm.url, 27)
      WHEN unnested_npm.url LIKE 'https://www.npmjs.com/package/%'
      THEN SUBSTRING(unnested_npm.url, 31)
      ELSE unnested_npm.url
    END AS artifact_name,
    unnested_npm.url AS artifact_url,
    'PACKAGE' AS artifact_type,
    projects.updated_at AS last_updated_at
  FROM projects
  CROSS JOIN UNNEST(projects.npm) AS @unnested_struct_ref(unnested_npm)
), 

-- Blockchain artifacts
blockchain_artifacts AS (
  SELECT
    projects.project_id,
    unnested_blockchain.address AS artifact_source_id,
    unnested_network AS artifact_source,
    '' AS artifact_namespace,
    unnested_blockchain.address AS artifact_name,
    unnested_blockchain.address AS artifact_url,
    unnested_tag AS artifact_type,
    projects.updated_at AS last_updated_at
  FROM projects
  CROSS JOIN UNNEST(projects.blockchain) AS @unnested_struct_ref(unnested_blockchain)
  CROSS JOIN UNNEST(unnested_blockchain.networks) AS @unnested_array_ref(unnested_network)
  CROSS JOIN UNNEST(unnested_blockchain.tags) AS @unnested_array_ref(unnested_tag)
), 

-- DeFiLlama protocols
defillama_artifacts AS (
  SELECT
    projects.project_id,
    LOWER(unnested_defillama.url) AS artifact_source_id,
    'DEFILLAMA' AS artifact_source,
    '' AS artifact_namespace,
    CASE
      WHEN unnested_defillama.url LIKE 'https://defillama.com/protocol/%'
      THEN SUBSTRING(unnested_defillama.url, 32)
      ELSE unnested_defillama.url
    END AS artifact_name,
    unnested_defillama.url AS artifact_url,
    'DEFILLAMA_PROTOCOL' AS artifact_type,
    projects.updated_at AS last_updated_at
  FROM projects
  CROSS JOIN UNNEST(projects.defillama) AS @unnested_struct_ref(unnested_defillama)
), 

-- Combine all artifact types
all_artifacts AS (
  SELECT * FROM website_artifacts
  UNION ALL
  SELECT * FROM farcaster_artifacts
  UNION ALL
  SELECT * FROM twitter_artifacts
  UNION ALL
  SELECT * FROM github_artifacts
  UNION ALL
  SELECT * FROM npm_artifacts
  UNION ALL
  SELECT * FROM blockchain_artifacts
  UNION ALL
  SELECT * FROM defillama_artifacts
)

-- Final output with standardized schema and generated artifact_id
SELECT
  @oso_entity_id(artifact_source, artifact_namespace, artifact_name) AS artifact_id,
  artifact_source_id,
  UPPER(artifact_source) AS artifact_source,
  LOWER(artifact_namespace) AS artifact_namespace,
  LOWER(artifact_name) AS artifact_name,
  LOWER(artifact_url) AS artifact_url,
  UPPER(artifact_type) AS artifact_type,
  project_id,
  last_updated_at
FROM all_artifacts
