MODEL (
  name oso.int_events__coresignal_venture,
  description 'All CoreSignal venture events (investments and rounds)',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  ),
  tags (
    "venture",
  ),
);

WITH base_events AS (
  SELECT DISTINCT
    announced_date AS time,
    company_id,
    company_name,
    'CORESIGNAL' AS event_source,
    UPPER(REPLACE(funding_round_name, ' ', '_')) AS funding_round_name,
    amount_raised,
    amount_raised_currency,
    num_investors,
    lead_investors
  FROM oso.stg_coresignal__funding_rounds
  WHERE announced_date IS NOT NULL
    AND funding_round_name IS NOT NULL
),

-- Investment received events (from company perspective)
investment_events AS (
  SELECT
    time,
    company_id,
    company_name,
    event_source,
    'INVESTMENT_RECEIVED' AS event_type,
    funding_round_name,
    amount_raised,
    amount_raised_currency,
    num_investors,
    NULL AS investor_name,
    NULL AS investor_id
  FROM base_events
),

-- Investment made events (from investor perspective) 
round_events AS (
  SELECT
    time,
    company_id,
    company_name,
    event_source,
    'LED_INVESTMENT_ROUND' AS event_type,
    funding_round_name,
    amount_raised,
    amount_raised_currency,
    num_investors,
    TRIM(BOTH '"' FROM investor_name::VARCHAR) AS investor_name,
    NULL::VARCHAR AS investor_id
  FROM base_events
  CROSS JOIN UNNEST(lead_investors) AS t(investor_name)
  WHERE investor_name IS NOT NULL
),

all_events AS (
  SELECT * FROM investment_events
  UNION ALL
  SELECT * FROM round_events
),

enriched_events AS (
  SELECT
    all_events.*,
    p2p.oso_project_id,
    p2p.oso_project_name,
    @oso_entity_id(artifact_fields.artifact_source, artifact_fields.artifact_namespace, artifact_fields.artifact_name) AS oso_artifact_id
  FROM all_events
  LEFT JOIN oso.int_project_to_projects__coresignal AS p2p
    ON all_events.company_id = p2p.coresignal_company_id
  CROSS JOIN LATERAL @create_ossd_funding_wallet_artifact(p2p.oso_project_name)
    AS artifact_fields
  WHERE p2p.is_best_match = TRUE
)

SELECT
  @oso_id(event_source, event_type, funding_round_name, company_id, time)
    AS event_id,
  time,
  event_source,
  event_type,
  funding_round_name,
  investor_name AS from_investor_name,
  investor_id AS from_investor_id,
  NULL::VARCHAR AS from_artifact_id,
  company_id AS to_company_id,
  company_name AS to_company_name,
  oso_project_id AS to_oso_project_id,
  oso_project_name AS to_oso_project_name,
  oso_artifact_id AS to_artifact_id,
  amount_raised,
  amount_raised_currency,
  num_investors
FROM enriched_events
