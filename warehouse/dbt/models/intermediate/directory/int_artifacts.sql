with all_artifacts as (
  {# 
    The `last_used` value is later used in this query to determine what the most
    _current_ name is. However, oss-directory names are considered canonical so
    `last_used` is only relevent for `git_user` artifacts.
  #}
  select
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_url,
    artifact_name
  from {{ ref('int_artifacts_by_project') }}
  union all
  select
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_url,
    MAX_BY(artifact_name, last_used) as artifact_name
  from {{ ref('int_artifacts_history') }}
  group by
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_url
)

select distinct
  {{ oso_id("artifact_source", "artifact_source_id") }} as artifact_id,
  artifact_source_id,
  artifact_source,
  artifact_namespace,
  artifact_name,
  artifact_url
from all_artifacts
