MODEL (
  name oso.int_events__coresignal_venture_rounds,
  description 'Intermediate table for Coresignal venture rounds',
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
    'INVESTMENT_MADE' AS event_type,
    UPPER(REPLACE(funding_round_name, ' ', '_')) AS funding_round_name,
    lead_investor,
    num_investors
  FROM oso.stg_coresignal__funding_rounds
),

enriched_events AS (
  SELECT
    events.*,
    p2p.oso_project_id,
    p2p.oso_project_name,
    p2p.artifact_source AS shared_artifact_source
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
  lead_investor,
  num_investors,
  coresignal_company_id,
  coresignal_company_name,
  oso_project_id,
  oso_project_name
FROM enriched_events
