{% set models = [
    'gas_fees_sum',
    'transactions_sum',
    'trusted_transactions_sum',
    'trusted_daily_active_users_avg',
    'trusted_monthly_active_users_avg',    
    'daily_active_addresses_avg',
    'monthly_active_addresses_avg',
    'trusted_users_onboarded_sum'
] %}

{% for model in models %}
  select * from {{ ref('superchain_metric__%s_6_months' % model) }}
  {% if not loop.last %}
    union all
  {% endif %}
{% endfor %}