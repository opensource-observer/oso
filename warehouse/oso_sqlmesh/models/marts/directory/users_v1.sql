MODEL (
  name oso.users_v1,
  kind FULL,
  tags (
    'export'
  )
);

SELECT
  users.user_id,
  users.user_source_id,
  users.user_source,
  users.display_name,
  users.profile_picture_url,
  users.bio,
  users.url
FROM oso.int_users AS users