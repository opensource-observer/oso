{#
  Get all passport scores
#}

select
  lower(p.passport_address as string) as passport_address,
  cast(p.evidence_rawScore as float) as evidence_rawScore,
  cast(p.evidence_threshold as float) as evidence_threshold,
  cast(p.last_score_update as timestamp) as last_score_update
from {{ source("gitcoin", "passport_scores") }} as p
