-- Hardcode round dates for legacy cGrants rounds
with round_dates as (
  select
    round_number,
    timestamp(date_round_started) as date_round_started,
    timestamp(date_round_ended) as date_round_ended
  from unnest([
    struct(
      1 as round_number,
      '2019-02-01T00:00:00Z' as date_round_started,
      '2019-02-15T00:00:00Z' as date_round_ended
    ),
    struct(2, '2019-03-26T00:00:00Z', '2019-04-19T00:00:00Z'),
    struct(3, '2019-09-15T00:00:00Z', '2019-10-04T00:00:00Z'),
    struct(4, '2020-01-06T00:00:00Z', '2020-01-21T00:00:00Z'),
    struct(5, '2020-03-23T00:00:00Z', '2020-04-05T00:00:00Z'),
    struct(6, '2020-06-16T00:00:00Z', '2020-07-03T00:00:00Z'),
    struct(7, '2020-09-14T00:00:00Z', '2020-10-02T18:00:00Z'),
    struct(8, '2020-12-02T00:00:00Z', '2020-12-18T00:00:00Z'),
    struct(9, '2021-03-10T00:00:00Z', '2021-03-26T00:00:00Z'),
    struct(10, '2021-06-16T15:00:00Z', '2021-07-02T00:00:00Z'),
    struct(11, '2021-09-08T15:00:00Z', '2021-09-24T00:00:00Z'),
    struct(12, '2021-12-01T15:00:00Z', '2021-12-17T00:00:00Z'),
    struct(13, '2022-03-09T15:00:00Z', '2022-03-25T00:00:00Z'),
    struct(14, '2022-06-08T15:00:00Z', '2022-06-24T00:00:00Z'),
    struct(15, '2022-09-07T15:00:00Z', '2022-09-23T00:00:00Z'),
    struct(16, '2023-01-17T00:00:00Z', '2023-01-31T00:00:00Z')
  ]) as v
),

round_details as (
  select
    round_id,
    round_name,
    coalesce(round_number, -1) as round_number,
    min(donation_timestamp) as date_round_started,
    max(donation_timestamp) as date_round_ended
  from {{ ref('stg_gitcoin__donations') }}
  group by round_id, round_number, round_name
),

matching as (
  select
    round_id,
    chain_id,
    coalesce(round_number, -1) as round_number,
    sum(amount_in_usd) as matching_amount_in_usd
  from {{ ref('stg_gitcoin__matching') }}
  group by round_id, round_number, chain_id
),

combined as (
  select
    matching.round_id,
    matching.round_number,
    matching.chain_id,
    matching.matching_amount_in_usd,
    coalesce(round_details.round_name, matching.round_id)
      as round_name,
    coalesce(round_details.date_round_started, round_dates.date_round_started)
      as date_round_started,
    coalesce(round_details.date_round_ended, round_dates.date_round_ended)
      as date_round_ended
  from matching
  left join round_details
    on
      matching.round_id = round_details.round_id
      and matching.round_number = round_details.round_number
  left join round_dates
    on matching.round_number = round_dates.round_number
  order by date_round_ended
)

select
  {{ oso_id("'GITCOIN'", 'round_id', 'round_number') }}
    as funding_round_id,
  round_id as gitcoin_round_id,
  round_number,
  round_name,
  chain_id,
  date_round_started,
  date_round_ended,
  matching_amount_in_usd
from combined
order by date_round_ended desc
