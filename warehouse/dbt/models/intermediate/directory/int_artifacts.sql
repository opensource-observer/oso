with ossd_artifacts as (
  select distinct
    artifact_source_id,
    artifact_namespace,
    artifact_type,
    artifact_url,
    LOWER(artifact_name) as artifact_name
  from {{ ref('int_ossd__artifacts_by_project') }}
),

from_artifacts as (
  {# `from` actor artifacts derived from all events #}
  select
    from_source_id as artifact_source_id,
    from_namespace as artifact_namespace,
    from_type as artifact_type,
    "" as artifact_url, {# for now this is blank #}
    LOWER(from_name) as artifact_name,
    MAX(e.time) as last_used
  from {{ ref('int_events') }} as e
  group by 1, 2, 3, 4, 5
),

all_artifacts as (
  {# 
    The `last_used` value is later used in this query to determine what the most
    _current_ name is. However, oss-directory names are considered canonical so
    we will use those by setting `last_used` to be the current timestamp.
  #}
  select
    oa.*,
    CURRENT_TIMESTAMP() as last_used
  from ossd_artifacts as oa
  union all
  select * from from_artifacts
)

select
  {{ oso_artifact_id("artifact") }} as artifact_id,
  artifact_source_id as artifact_source_id,
  artifact_namespace as artifact_namespace,
  artifact_type as artifact_type,
  artifact_url as artifact_url,
  MAX_BY(artifact_name, last_used) as artifact_name,
  TO_JSON(ARRAY_AGG(distinct artifact_name)) as artifact_name_array
from all_artifacts
group by 1, 2, 3, 4, 5
