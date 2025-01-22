select distinct
  gitcoin_project_id,
  latest_project_github,
  latest_project_recipient_address,
  oso_wallet_match,
  oso_repo_match,
  oso_project_id,
  oso_project_name,
  oso_display_name
from {{ ref('int_gitcoin_project_directory') }}
