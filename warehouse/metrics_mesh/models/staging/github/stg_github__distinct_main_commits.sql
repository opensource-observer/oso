MODEL (
  name metrics.stg_github__distinct_main_commits,
  description 'Gathers all github commits on the default branch of a repo that are distinct.',
  kind FULL,
);

{#
  Gathers all github commits on the default branch of a repo that are distinct.

  We use the `MIN_BY` method here to grab the first occurrence of a given commit
  in the case of duplicated event counts (which does seem to happen with some
  frequency)
#}
select
  ghc.repository_id,
  ghc.sha,
  MIN(ghc.created_at) as created_at,
  MIN_BY(ghc.repository_name, ghc.created_at) as repository_name,
  MIN_BY(ghc.push_id, ghc.created_at) as push_id,
  MIN_BY(ghc.ref, ghc.created_at) as ref,
  MIN_BY(ghc.actor_id, ghc.created_at) as actor_id,
  MIN_BY(ghc.actor_login, ghc.created_at) as actor_login,
  MIN_BY(ghc.author_email, ghc.created_at) as author_email,
  MIN_BY(ghc.author_name, ghc.created_at) as author_name,
  MIN_BY(ghc.is_distinct, ghc.created_at) as is_distinct,
  MIN_BY(ghc.api_url, ghc.created_at) as api_url
from metrics.stg_github__commits as ghc
inner join metrics.stg_ossd__current_repositories as repos
  on ghc.repository_id = repos.id
where ghc.ref = CONCAT('refs/heads/', repos.branch)

{# 
  We group by the repository id and sha to prevent merging commits between forks
  and in cases where duplicate shas exist between different repos
#}
group by ghc.repository_id, ghc.sha
