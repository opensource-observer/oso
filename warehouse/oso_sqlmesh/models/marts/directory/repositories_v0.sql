model(name oso.repositories_v0, kind full)
;

select
    project_id,
    artifact_id,
    artifact_source_id,
    artifact_source,
    artifact_namespace,
    artifact_name,
    artifact_url,
    is_fork,
    branch,
    star_count,
    watcher_count,
    fork_count,
    license_name,
    license_spdx_id,
    "language",
    created_at,
    updated_at
from oso.int_repositories
