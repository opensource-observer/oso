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
    company_id AS coresignal_company_id,
    company_name AS coresignal_company_name,
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
    coresignal_company_id,
    coresignal_company_name,
    event_source,
    'INVESTMENT_RECEIVED' AS event_type,
    funding_round_name,
    amount_raised,
    amount_raised_currency,
    num_investors,
    NULL AS lead_investor
  FROM base_events
),

-- Investment made events (from investor perspective) 
round_events AS (
  SELECT
    time,
    coresignal_company_id,
    coresignal_company_name,
    event_source,
    'INVESTMENT_MADE' AS event_type,
    funding_round_name,
    amount_raised,
    amount_raised_currency,
    num_investors,
    TRIM(BOTH '"' FROM lead_investor::VARCHAR) AS lead_investor
  FROM base_events
  CROSS JOIN UNNEST(lead_investors) AS t(lead_investor)
  WHERE lead_investor IS NOT NULL
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
    p2p.oso_project_name
  FROM all_events
  LEFT JOIN oso.int_project_to_projects__coresignal AS p2p
    ON all_events.coresignal_company_id = p2p.coresignal_company_id
)

SELECT
  @oso_id(event_source, event_type, funding_round_name, coresignal_company_id, time)
    AS event_id,
  time,
  event_source,
  event_type,
  funding_round_name,
  lead_investor,
  num_investors,
  coresignal_company_id,
  coresignal_company_name,
  oso_project_id,
  oso_project_name,
  amount_raised,
  amount_raised_currency
FROM enriched_events
