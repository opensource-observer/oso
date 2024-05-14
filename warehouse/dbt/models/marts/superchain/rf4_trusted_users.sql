with user_model as (
  select
  artifacts_by_user.user_id,
  artifacts_by_user.user_source,
  artifacts_by_user.user_source_id,
  artifacts_by_user.artifact_name,
  null as eigentrust_verification,
  passport_scores.evidence_rawScore
    >= passport_scores.evidence_threshold as passport_verification  
  from {{ ref('int_artifacts_by_user') }} as artifacts_by_user
  left {{ ref('stg_passport__scores') }} as passport_scores
    on artifacts_by_user.artifact_name = passport_scores.passport_address
)

select
  user_id,
  user_source,
  user_source_id,
  artifact_name
from user_model
where
  passport_verification = true
  or eigentrust_verification = true
