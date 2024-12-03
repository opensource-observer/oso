with partner_rounds as (
  select *
  from {{ ref('int_gitcoin_funding_events') }}
  where
    round_type = 'PartnerRound'
    and round_name is not null
),

main_rounds as (
  select *
  from {{ ref('int_gitcoin_funding_events') }}
  where round_type = 'MainRound'
),

unioned as (
  select * from partner_rounds
  union all
  select * from main_rounds
)

select
  gitcoin_data_source,
  gitcoin_round_id,
  round_number,
  round_name,
  round_type,
  main_round_label,
  array_agg(distinct chain_id) as chain_ids,
  sum(amount_in_usd) as total_amount_in_usd,
  count(distinct gitcoin_project_id) as count_projects
from unioned
group by
  gitcoin_data_source,
  gitcoin_round_id,
  round_number,
  round_name,
  round_type,
  main_round_label
order by
  round_type asc,
  main_round_label desc,
  gitcoin_round_id asc
