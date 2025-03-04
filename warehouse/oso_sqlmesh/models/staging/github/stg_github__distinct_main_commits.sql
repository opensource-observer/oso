model(
    name oso.stg_github__distinct_main_commits,
    description 'Gathers all github commits on the default branch of a repo that are distinct.',
    kind full,
)
;

{#
  Gathers all github commits on the default branch of a repo that are distinct.

  We use the `MIN_BY` method here to grab the first occurrence of a given commit
  in the case of duplicated event counts (which does seem to happen with some
  frequency)
#}
select
    ghc.repository_id,
    ghc.sha,
    min(ghc.created_at) as created_at,
    min_by(ghc.repository_name, ghc.created_at) as repository_name,
    min_by(ghc.push_id, ghc.created_at) as push_id,
    min_by(ghc.ref, ghc.created_at) as ref,
    min_by(ghc.actor_id, ghc.created_at) as actor_id,
    min_by(ghc.actor_login, ghc.created_at) as actor_login,
    min_by(ghc.author_email, ghc.created_at) as author_email,
    min_by(ghc.author_name, ghc.created_at) as author_name,
    min_by(ghc.is_distinct, ghc.created_at) as is_distinct,
    min_by(ghc.api_url, ghc.created_at) as api_url
from oso.stg_github__commits as ghc
inner join oso.stg_ossd__current_repositories as repos on ghc.repository_id = repos.id
where ghc.ref = concat('refs/heads/', repos.branch)

{# 
  We group by the repository id and sha to prevent merging commits between forks
  and in cases where duplicate shas exist between different repos
#}
group by ghc.repository_id, ghc.sha
