MODEL (
  name metrics.int_superchain_code_dependencies,
  kind FULL,
);

@DEF(max_release_lookback_days, 180);

with all_dependencies as (
  select distinct
    sbom.project_id as dependent_project_id,
    sbom.artifact_id as dependent_artifact_id,
    sbom.package_github_project_id as dependency_project_id,
    sbom.package_github_artifact_id as dependency_artifact_id,
    sbom.package_artifact_source as dependency_source,
    sbom.package_artifact_name as dependency_name,
    releases.latest_package_release as dependency_release_date
  from metrics.int_sbom_artifacts as sbom
  inner join metrics.int_latest_release_by_repo as releases
    on sbom.package_github_artifact_id = releases.artifact_id
)

select
  all_dependencies.*,
  case
    when date(dependency_release_date) >= (current_date() - interval @max_release_lookback_days day)
    then true
    else false
  end as devtool_has_recent_release,
  case when dependent_project_id in (
    select distinct project_id
    from metrics.int_superchain_s7_onchain_builder_eligibility
    where is_eligible
  ) then true else false end as dependent_is_eligible
from all_dependencies
where
  dependency_project_id != dependent_project_id