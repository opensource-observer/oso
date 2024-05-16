{#
  This is a base model one can import into other to filter for the playground
#}
{{
  config(
    materialized="ephemeral"
  ) if target.name in ['production', 'base_playground'] else config(
    enabled=false,
  )
}}
SELECT * FROM UNNEST([
  "gitcoin",
  "opensource-observer",
  "uniswap",
  "velodrome",
  "ethereum-attestation-service",
  "zora",
  "libp2p",
  "rabbit-hole",
  "safe-global",
  "aave"
]) as project_name