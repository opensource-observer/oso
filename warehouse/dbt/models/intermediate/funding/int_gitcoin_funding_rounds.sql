-- Hardcode the cGrant funding round dates
with round_dates as (
  select
    round_num,
    timestamp(`start_date`) as date_round_started,
    timestamp(`end_date`) as date_round_ended
  from unnest([
    struct(
      1 as round_num,
      '2019-02-01T00:00:00Z' as `start_date`,
      '2019-02-15T00:00:00Z' as `end_date`
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

-- Process legacy cGrants platform data
cgrants as (
  select
    grants.round_id as gitcoin_round_id,
    grants.round_number,
    grants.round_id as round_name,
    round_dates.date_round_started,
    round_dates.date_round_ended,
    'quadratic_funding' as allocation_strategy,
    'cgrants' as platform,
    round(grants.matching_amount_in_usd, 2) as matching_amount_in_usd,
    grants.chain_ids
  from (
    select
      round_number,
      round_id,
      array_agg(distinct chain_id) as chain_ids,
      sum(amount_in_usd) as matching_amount_in_usd
    from {{ ref('stg_gitcoin__matching') }}
    where round_number is not null and round_number <= 16
    group by round_number, round_id
  ) as grants
  left join round_dates as round_dates
    on grants.round_number = round_dates.round_num
  order by round_dates.date_round_started
),

-- Process Grants Stack platform data
grants_stack as (
  select
    round_id as gitcoin_round_id,
    coalesce(round_num, -1) as round_number,
    round_name,
    date_round_started,
    date_round_ended,
    'quadratic_funding' as allocation_strategy,
    'grants_stack' as platform,
    round(sum(matching_pool), 2) as matching_amount_in_usd,
    array_agg(distinct chain_id) as chain_ids
  from {{ source('static_data_sources', 'grants_stack_rounds') }}
  where round_id is not null
  group by round_id, round_num, round_name, date_round_started, date_round_ended
),

-- Process current Allo platform data
allo as (
  select
    round_id as gitcoin_round_id,
    round_number,
    round_name,
    date_round_started,
    date_round_ended,
    'quadratic_funding' as allocation_strategy,
    'allo' as platform,
    matching_amount_in_usd,
    chain_ids
  from (
    select
      round_id,
      coalesce(round_number, -1) as round_number,
      'tbc' as round_name,
      min(timestamp(`timestamp`)) as date_round_started,
      max(timestamp(`timestamp`)) as date_round_ended,
      round(sum(amount_in_usd), 2) as matching_amount_in_usd,
      array_agg(distinct chain_id) as chain_ids
    from {{ ref('stg_gitcoin__matching') }}
    where
      (round_number is null or round_number > 16)
      and round_id not in (select distinct gitcoin_round_id from grants_stack)
    group by round_id, round_number
  )
),

union_all as (
  select * from cgrants
  union all
  select * from grants_stack
  union all
  select * from allo
)

select
  {{ oso_id("'GITCOIN'", 'gitcoin_round_id', 'round_number') }}
    as funding_round_id,
  *
from union_all
order by date_round_ended desc
