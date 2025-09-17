MODEL (
  name oso.int_events__coresignal_investments_to_projects,
  description 'Intermediate table for Coresignal venture investments to projects',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  ),
  tags (
    "venture",
  ),
);

WITH events AS (
  SELECT DISTINCT
    announced_date AS time,
    company_id AS coresignal_company_id,
    company_name AS coresignal_company_name,
    'CORESIGNAL' AS event_source,
    'INVESTMENT_RECEIVED' AS event_type,
    UPPER(REPLACE(funding_round_name, ' ', '_')) AS funding_round_name,
    amount_raised,
    amount_raised_currency
  FROM oso.stg_coresignal__funding_rounds
),

enriched_events AS (
  SELECT
    events.*,
    p2p.oso_project_id,
    p2p.oso_project_name
  FROM events
  LEFT JOIN oso.int_project_to_projects__coresignal AS p2p
    ON events.coresignal_company_id = p2p.coresignal_company_id
    AND p2p.is_best_match = true
)

SELECT
  @oso_id(event_source, funding_round_name, coresignal_company_id, time)
    AS event_id,
  time,    
  event_source,
  event_type,
  funding_round_name,
  coresignal_company_id,
  coresignal_company_name,
  oso_project_id,
  oso_project_name,
  amount_raised,
  amount_raised_currency
FROM enriched_events