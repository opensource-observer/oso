{{ 
  config(
    materialized='table',
    meta = {
      'sync_to_db': True,
      'index': {
        'idx_artifact_id': ["from_artifact_id"],
        'idx_artifact_name': ["from_artifact_source", "from_artifact_namespace", "from_artifact_name"],
        'idx_package_artifact': ["to_package_artifact_source", "to_package_artifact_name"],
        'idx_package_github': ["to_package_github_owner", "to_package_github_repo"]
      }
    }
  )
}}


select distinct
  artifact_id as from_artifact_id,
  artifact_source as from_artifact_source,
  artifact_namespace as from_artifact_namespace,
  artifact_name as from_artifact_name,
  package_artifact_id as to_package_artifact_id,
  package_artifact_source as to_package_artifact_source,
  package_artifact_name as to_package_artifact_name,
  package_github_owner as to_package_github_owner,
  package_github_repo as to_package_github_repo,
  package_github_artifact_id as to_package_github_artifact_id
from {{ ref('int_sbom_artifacts') }}
