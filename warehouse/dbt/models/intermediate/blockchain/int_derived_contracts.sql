{% set networks = [
		"ethereum", "optimism", 
		"base", "frax", 
		"mode", "pgn", "zora"
	] 
%}
with {% for network in networks %}
  {{ network }}_factories_and_deployers as (
    select
      factories.block_timestamp as block_timestamp,
      factories.transaction_hash as transaction_hash,
      deployers.deployer_address as deployer_address,
      factories.contract_address as contract_address
    from {{ ref("stg_%s__factories" % network) }} as factories
    inner join {{ ref("stg_%s__deployers" % network) }} as deployers
      on factories.factory_address = deployers.contract_address
    union all
    select
      block_timestamp,
      transaction_hash,
      deployer_address,
      contract_address
    from {{ ref("stg_%s__deployers" % network) }}
  ){% if not loop.last %},{% endif %}
{% endfor %}
{% for network in networks %}
  {% if not loop.first %}
    union all
  {% endif %}
  select
    block_timestamp,
    transaction_hash,
    "{{ network.upper() }}" as network,
    deployer_address,
    contract_address
  from {{ network }}_factories_and_deployers
{% endfor %}
