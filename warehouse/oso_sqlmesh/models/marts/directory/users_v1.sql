MODEL (
  name metrics.users_v1,
  kind FULL,
  tags (
    'export'
  ),
);

select
  users.user_id,
  users.user_source_id,
  users.user_source,
  users.display_name,
  users.profile_picture_url,
  users.bio,
  users.url
from metrics.int_users as users