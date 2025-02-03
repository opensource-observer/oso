{{
  config(
    materialized='table'
  )
}}

{% set columns = [
    "id", "legacy_id", "group", "type", "kind", "description", "amount", 
    "amount_in_host_currency", "host_currency_fx_rate", "net_amount", 
    "net_amount_in_host_currency", "tax_amount", "tax_info", "platform_fee", 
    "host_fee", "payment_processor_fee", "account", "from_account", 
    "to_account", "expense", "order", "created_at", "updated_at", 
    "is_refunded", "is_refund", "is_disputed", "is_in_review", 
    "payment_method", "payout_method", "is_order_rejected", "merchant_id", 
    "invoice_template", "host"
] %}

with source as (
  select * from {{ source('open_collective', 'deposits') }}
),

renamed as (
  select
    {% for column in columns %}
      {{ adapter.quote(column) }}{% if not loop.last %},{% endif %}
    {% endfor %}
  from source
)

select * from renamed
