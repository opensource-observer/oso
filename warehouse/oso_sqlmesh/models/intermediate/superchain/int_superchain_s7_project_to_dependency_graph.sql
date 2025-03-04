model(
    name oso.int_superchain_s7_project_to_dependency_graph,
    description "Maps relationships between onchain builder projects and their devtooling dependencies",
    kind incremental_by_time_range(
        time_column sample_date, batch_size 90, batch_concurrency 1, lookback 7
    ),
    start '2015-01-01',
    cron '@daily',
    partitioned_by day("sample_date"),
    grain(
        sample_date,
        onchain_builder_project_id,
        devtooling_project_id,
        dependent_artifact_id,
        dependency_artifact_id
    )
)
;

with
    onchain_builder_projects as (
        select
            project_id as onchain_builder_project_id,
            is_eligible,
            cast(sample_date as timestamp) as sample_date
        from oso.int_superchain_s7_onchain_builder_eligibility
    ),

    devtooling_projects as (
        select
            project_id as devtooling_project_id,
            repo_artifact_id,
            is_eligible,
            cast(sample_date as timestamp) as sample_date
        from oso.int_superchain_s7_devtooling_repo_eligibility
    )

select
    onchain_builder_projects.sample_date,
    onchain_builder_projects.onchain_builder_project_id,
    devtooling_projects.devtooling_project_id,
    dependencies.dependent_artifact_id,
    dependencies.dependency_artifact_id,
    dependencies.dependency_name,
    dependencies.dependency_source
from oso.int_code_dependencies as dependencies
inner join
    oso.int_repositories_enriched as dependents
    on dependencies.dependent_artifact_id = dependents.artifact_id
inner join
    onchain_builder_projects
    on dependents.project_id = onchain_builder_projects.onchain_builder_project_id
inner join
    devtooling_projects
    on dependencies.dependency_artifact_id = devtooling_projects.repo_artifact_id
    and onchain_builder_projects.sample_date = devtooling_projects.sample_date
where
    onchain_builder_projects.onchain_builder_project_id
    != devtooling_projects.devtooling_project_id
    and onchain_builder_projects.is_eligible
    and devtooling_projects.is_eligible
