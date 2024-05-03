{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

select
  users.user_id,
  users.user_source_id,
  users.user_source,
  users.display_name,
  users.profile_picture_url,
  users.bio,
  users.url
from {{ ref('int_users') }} as users
