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
    recipient_address AS to_artifact_name,
    donor_address AS from_artifact_name,
    transaction_hash,
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
    matching.recipient_address AS to_artifact_name,
    'gitcoin' AS from_artifact_name,
    NULL AS transaction_hash,
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
    to_artifact_name,
    from_artifact_name,
    transaction_hash,
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
    to_artifact_name,
    from_artifact_name,
    transaction_hash,
    amount_in_usd
  FROM matching
),

chain_mappings AS (
  SELECT DISTINCT
    chain_id,
    CASE
      WHEN chain_id = '1' THEN 'MAINNET'
      WHEN chain_id = '137' THEN 'POLYGON'
      WHEN chain_id = '42161' THEN 'ARBITRUM_ONE'
      WHEN chain_id = '1329' THEN 'BASE'
      WHEN chain_id = '424' THEN 'AVALANCHE'
      WHEN chain_id = '10' THEN 'OPTIMISM'
      WHEN chain_id = '42220' THEN 'CELO'
      WHEN chain_id = '43114' THEN 'AVALANCHE'
      WHEN chain_id = '42' THEN 'KOVAN'
      WHEN chain_id = '1088' THEN 'METIS'
      WHEN chain_id = '324' THEN 'ZKSYNC_ERA'
      WHEN chain_id = '250' THEN 'FANTOM'
      WHEN chain_id = '534352' THEN 'SCROLL'
      WHEN chain_id = '8453' THEN 'BASE'
      ELSE 'UNKNOWN'
    END AS chain
  FROM unioned_events
),

mapped_events AS (
  SELECT
    events.time,
    events.event_source,
    events.round_id,
    events.round_number,
    events.chain_id,
    chain_mappings.chain AS chain,
    events.round_name,
    events.gitcoin_project_id,
    events.gitcoin_project_name,
    project_lookup.group_id AS gitcoin_group_id,
    project_summary.project_application_title AS gitcoin_group_project_name,
    events.to_artifact_name,
    events.from_artifact_name,
    events.transaction_hash,
    events.amount_in_usd
  FROM unioned_events AS events
  JOIN chain_mappings
    ON events.chain_id = chain_mappings.chain_id
  JOIN oso.stg_gitcoin__project_lookup AS project_lookup
    ON events.gitcoin_project_id = project_lookup.project_id
  JOIN oso.stg_gitcoin__project_groups_summary AS project_summary
    ON project_lookup.group_id = project_summary.group_id
)

SELECT
  time,
  event_source,
  gitcoin_group_project_name,
  gitcoin_project_name,
  chain,
  round_number,
  round_name,
  to_artifact_name,
  from_artifact_name,
  amount_in_usd,
  transaction_hash,
  round_id,
  chain_id,
  @oso_entity_id(chain, '', to_artifact_name) AS to_artifact_id,
  @oso_entity_id(chain, '', from_artifact_name) AS from_artifact_id,
  gitcoin_group_id,
  gitcoin_project_id
FROM mapped_events