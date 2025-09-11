MODEL (
  name oso.stg_coresignal__funding_rounds,
  description 'Funding rounds data from Core Signal API',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH base_data AS (
  SELECT
    cd.id::BIGINT AS company_id,
    cd.company_name::VARCHAR AS company_name,
    JSON_EXTRACT_SCALAR(fr, '$.name') AS funding_round_name,
    CAST(JSON_EXTRACT_SCALAR(fr, '$.announced_date') AS DATE) AS announced_date,
    CAST(JSON_EXTRACT(fr, '$.lead_investors') AS ARRAY(VARCHAR)) AS lead_investors,
    JSON_EXTRACT_SCALAR(fr, '$.amount_raised') AS amount_raised,
    JSON_EXTRACT_SCALAR(fr, '$.amount_raised_currency') AS amount_raised_currency,
    JSON_EXTRACT_SCALAR(fr, '$.num_investors') AS num_investors
  FROM @oso_source('bigquery_oso_dynamic.oso.coresignal_company_data') AS cd
  CROSS JOIN UNNEST(CAST(funding_rounds as ARRAY(JSON))) AS t(fr)
)

SELECT DISTINCT
  company_id,
  company_name,
  funding_round_name,
  announced_date,
  amount_raised,
  amount_raised_currency,
  num_investors,
  TRIM(BOTH '"' FROM lead_investor::VARCHAR) AS lead_investor
FROM base_data
CROSS JOIN UNNEST(lead_investors) AS t(lead_investor)
WHERE lead_investor IS NOT NULL
