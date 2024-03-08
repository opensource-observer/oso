SELECT * FROM {{ ref('stg_dune__optimism_contract_invocation') }}
UNION ALL
SELECT * FROM {{ ref('stg_dune__arbitrum_contract_invocation') }}
