MODEL (
  name oso.int_events__gitcoin_funding,
  description 'Intermediate table for Gitcoin funding events',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  ),
  tags (
    "funding",
  ),
);


WITH donations AS (
  SELECT
    timestamp AS time,
    'GITCOIN_DONATIONS' AS event_source,
    round_id,
    round_number,
    chain_id,
    round_name,
    project_id AS gitcoin_project_id,
    project_name AS gitcoin_project_name,
    recipient_address,
    donor_address,
    amount_in_usd
  FROM oso.stg_gitcoin__all_donations
  WHERE amount_in_usd > 0
),

rounds AS (
  SELECT DISTINCT
    round_id,
    chain_id,
    round_name,
    MAX(time) AS end_time
  FROM donations
  WHERE round_id IS NOT NULL
  GROUP BY 1, 2, 3
),

matching AS (
  SELECT
    COALESCE(matching.timestamp, rounds.end_time) AS time,
    'GITCOIN_MATCHING' AS event_source,
    matching.round_id,
    matching.round_number,
    matching.chain_id,
    rounds.round_name,
    matching.project_id AS gitcoin_project_id,
    matching.title AS gitcoin_project_name,    
    matching.recipient_address,
    NULL::VARCHAR AS donor_address,
    matching.match_amount_in_usd AS amount_in_usd
  FROM oso.stg_gitcoin__all_matching AS matching
  JOIN rounds AS rounds
    ON matching.round_id = rounds.round_id
    AND matching.chain_id = rounds.chain_id
  WHERE matching.match_amount_in_usd > 0
),

unioned_events AS (
  SELECT
    time,
    event_source,
    round_id,
    round_number,
    chain_id,
    round_name,
    gitcoin_project_id,
    gitcoin_project_name,
    recipient_address,
    donor_address,
    amount_in_usd
  FROM donations
  UNION ALL
  SELECT
    time,
    event_source,
    round_id,
    round_number,
    chain_id,
    round_name,
    gitcoin_project_id,
    gitcoin_project_name,
    recipient_address,
    donor_address,
    amount_in_usd
  FROM matching
),

project_to_projects AS (
  SELECT DISTINCT
    gitcoin_project_id,
    oso_project_id,
    oso_project_name
  FROM oso.int_project_to_projects__gitcoin
  WHERE is_best_match = TRUE
),

enriched_events AS (
  SELECT
    events.time,
    events.event_source,
    events.round_id,
    events.round_number,
    events.chain_id,
    @chain_id_to_chain_name(events.chain_id) AS chain,
    events.round_name,
    events.gitcoin_project_id,
    events.gitcoin_project_name,
    project_lookup.group_id AS gitcoin_group_id,
    project_summary.project_application_title AS gitcoin_group_project_name,
    events.recipient_address,
    events.donor_address,
    events.amount_in_usd,
    project_to_projects.oso_project_id,
    project_to_projects.oso_project_name
  FROM unioned_events AS events
  JOIN oso.stg_gitcoin__project_lookup AS project_lookup
    ON events.gitcoin_project_id = project_lookup.project_id
  JOIN oso.stg_gitcoin__project_groups_summary AS project_summary
    ON project_lookup.group_id = project_summary.group_id
  LEFT JOIN project_to_projects
    ON events.gitcoin_group_id = project_to_projects.gitcoin_group_id
)

SELECT
  time,
  event_source,
  gitcoin_group_project_name,
  gitcoin_project_name,
  recipient_address,
  donor_address,
  amount_in_usd,
  round_number,
  round_name,
  chain,
  chain_id,
  round_id,
  gitcoin_group_id,
  gitcoin_project_id,
  oso_project_id,
  oso_project_name
FROM enriched_events