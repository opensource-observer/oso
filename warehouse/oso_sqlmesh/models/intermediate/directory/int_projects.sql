model(name oso.int_projects, description 'All projects', kind full)
;

with
    ossd_projects as (
        select
            project_id,
            project_source,
            project_namespace,
            project_name,
            display_name,
            description
        from oso.stg_ossd__current_projects
    ),

    op_atlas_projects as (
        select
            project_id,
            project_source,
            project_namespace,
            project_name,
            display_name,
            description
        from oso.stg_op_atlas_project
    )

select *
from ossd_projects
union all
select *
from op_atlas_projects
