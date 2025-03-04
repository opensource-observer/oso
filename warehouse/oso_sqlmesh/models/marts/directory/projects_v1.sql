model(name oso.projects_v1, kind full, tags('export'),)
;

select
    projects.project_id,
    projects.project_source,
    projects.project_namespace,
    projects.project_name,
    projects.display_name,
    projects.description
from oso.int_projects as projects
