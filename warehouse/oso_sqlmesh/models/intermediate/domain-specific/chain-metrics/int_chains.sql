MODEL(
  name oso.int_chains,
  description 'OSO Chains',
  dialect trino,
  kind full,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH l2beat_chains AS (
 SELECT DISTINCT
    UPPER(COALESCE(chain_alias.oso_chain_name, projects.slug)) AS chain
  FROM oso.stg_l2beat__projects AS projects
  LEFT JOIN oso.seed_chain_alias_to_chain_name AS chain_alias
    ON UPPER(projects.slug) = UPPER(chain_alias.chain_alias)
    AND chain_alias.source = 'l2beat'
  WHERE type = 'layer2'
),

defillama_chains AS (
  SELECT DISTINCT
    UPPER(COALESCE(chain_alias.oso_chain_name, dl.chain)) AS chain
  FROM oso.stg_defillama__historical_chain_tvl AS dl
  LEFT JOIN oso.seed_chain_alias_to_chain_name AS chain_alias
    ON UPPER(dl.chain) = UPPER(chain_alias.chain_alias)
    AND chain_alias.source = 'defillama'
  WHERE
    dl.tvl >= 10000000
    AND dl.time >= CURRENT_DATE - INTERVAL '1' YEAR
),

superchain_chains AS (
  SELECT DISTINCT chain
  FROM oso.int_superchain_chain_names
  WHERE chain NOT IN ('ETHEREUM')
),

all_chains AS (
  SELECT * FROM l2beat_chains
  UNION ALL
  SELECT * FROM defillama_chains
  UNION ALL
  SELECT * FROM superchain_chains
),

distinct_chains AS (
  SELECT DISTINCT
    chain
  FROM all_chains
)

SELECT
  chain,
  chain IN (SELECT chain FROM superchain_chains) AS is_superchain,
  chain IN (SELECT chain FROM l2beat_chains) AS is_layer2,
  chain IN (SELECT chain FROM defillama_chains) AS has_tvl
FROM distinct_chains