MODEL (
  name oso.int_users,
  description 'All users',
  kind FULL
);

WITH farcaster_users AS (
  SELECT
    user_id,
    farcaster_id AS user_source_id,
    'FARCASTER' AS user_source,
    display_name,
    profile_picture_url,
    bio,
    url
  FROM oso.stg_farcaster__profiles
), lens_users AS (
  SELECT
    user_id,
    lens_profile_id AS user_source_id,
    'LENS' AS user_source,
    full_name AS display_name,
    profile_picture_url,
    bio,
    '' AS url
  FROM oso.stg_lens__profiles
), github_users AS (
  SELECT
    from_artifact_id AS user_id,
    from_artifact_source_id AS user_source_id,
    'GITHUB' AS user_source,
    display_name,
    '' AS profile_picture_url,
    '' AS bio,
    'https://github.com/' || display_name AS url
  FROM (
    SELECT
      from_artifact_id,
      from_artifact_source_id,
      ARG_MAX(LOWER(from_artifact_name), time) AS display_name
    FROM oso.int_events__github
    GROUP BY
      from_artifact_id,
      from_artifact_source_id
  )
)
SELECT
  *
FROM farcaster_users
UNION ALL
SELECT
  *
FROM lens_users
UNION ALL
SELECT
  *
FROM github_users