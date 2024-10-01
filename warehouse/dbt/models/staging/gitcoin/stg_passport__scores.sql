{#
  Get all passport scores
#}

select
  LOWER(p.passport_address) as passport_address,
  CAST(p.evidence_rawscore as numeric) as evidence_rawscore,
  CAST(p.evidence_threshold as numeric) as evidence_threshold,
  CAST(p.last_score_timestamp as timestamp) as last_score_timestamp
from {{ source("gitcoin", "passport_scores") }} as p
