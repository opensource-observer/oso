select * from {{ ref('stg_dune__optimism_contract_invocation') }}
union all
select * from {{ ref('stg_dune__arbitrum_contract_invocation') }}
