{{
  config(
    materialized='table'
  )
}}


select distinct
  sbom.project_id as dependent_project_id,
  sbom.artifact_id as dependent_artifact_id,
  sbom.package_github_project_id as dependency_project_id,
  sbom.package_github_artifact_id as dependency_artifact_id,
  sbom.package_artifact_name as dependency_name,
  sbom.package_artifact_source as dependency_source
from {{ ref('int_sbom_artifacts') }} as sbom
inner join {{ ref('int_superchain_s7_onchain_builder_eligibility') }} as ocr
  on sbom.project_id = ocr.project_id
inner join {{ ref('int_superchain_s7_devtooling_eligibility') }} as dtr
  on sbom.package_github_artifact_id = dtr.repo_artifact_id
where
  sbom.project_id != sbom.package_github_project_id
  and ocr.is_eligible
  and dtr.is_eligible
