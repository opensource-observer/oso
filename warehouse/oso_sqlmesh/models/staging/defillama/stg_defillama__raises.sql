MODEL (
  name oso.stg_defillama__raises,
  description 'Raise events data from DefiLlama API, with one row per investor per raise',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH base_raises AS (
  SELECT
    date::TIMESTAMP AS announced_date,
    name::VARCHAR AS company_name,
    round::VARCHAR AS funding_round_name,
    amount::DOUBLE AS amount_raised,
    CAST(JSON_EXTRACT(chains, '$') AS ARRAY(VARCHAR)) AS chains,
    sector::VARCHAR AS sector,
    category::VARCHAR AS category,
    category_group::VARCHAR AS category_group,
    source::VARCHAR AS source,
    CAST(JSON_EXTRACT(lead_investors, '$') AS ARRAY(VARCHAR)) AS lead_investors,
    CAST(JSON_EXTRACT(other_investors, '$') AS ARRAY(VARCHAR)) AS other_investors,
    defillama_id::VARCHAR AS company_id,
    valuation::DOUBLE AS valuation
  FROM @oso_source('bigquery.defillama.raises')
),

lead_investors_unpacked AS (
  SELECT
    *,
    investor AS investor_name,
    'LEAD' AS investor_type
  FROM base_raises
  CROSS JOIN UNNEST(lead_investors) AS t(investor)
),

other_investors_unpacked AS (
  SELECT
    *,
    investor AS investor_name,
    'OTHER' AS investor_type
  FROM base_raises
  CROSS JOIN UNNEST(other_investors) AS t(investor)
)

SELECT
  announced_date,
  company_name,
  funding_round_name,
  amount_raised,
  chains,
  sector,
  category,
  category_group,
  source,
  company_id,
  valuation,
  investor_name,
  investor_type
FROM lead_investors_unpacked

UNION ALL

SELECT
  announced_date,
  company_name,
  funding_round_name,
  amount_raised,
  chains,
  sector,
  category,
  category_group,
  source,
  company_id,
  valuation,
  investor_name,
  investor_type
FROM other_investors_unpacked
