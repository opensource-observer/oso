with source as (
  select * from {{ source('open_collective', 'expenses') }}
),

renamed as (
  select
    {{ adapter.quote("id") }},
    {{ adapter.quote("legacy_id") }},
    {{ adapter.quote("group") }},
    {{ adapter.quote("type") }},
    {{ adapter.quote("kind") }},
    {{ adapter.quote("description") }},
    {{ adapter.quote("amount") }},
    {{ adapter.quote("amount_in_host_currency") }},
    {{ adapter.quote("host_currency_fx_rate") }},
    {{ adapter.quote("net_amount") }},
    {{ adapter.quote("net_amount_in_host_currency") }},
    {{ adapter.quote("tax_amount") }},
    {{ adapter.quote("tax_info") }},
    {{ adapter.quote("platform_fee") }},
    {{ adapter.quote("host_fee") }},
    {{ adapter.quote("payment_processor_fee") }},
    {{ adapter.quote("account") }},
    {{ adapter.quote("from_account") }},
    {{ adapter.quote("to_account") }},
    {{ adapter.quote("expense") }},
    {{ adapter.quote("order") }},
    {{ adapter.quote("created_at") }},
    {{ adapter.quote("updated_at") }},
    {{ adapter.quote("is_refunded") }},
    {{ adapter.quote("is_refund") }},
    {{ adapter.quote("is_disputed") }},
    {{ adapter.quote("is_in_review") }},
    {{ adapter.quote("payment_method") }},
    {{ adapter.quote("payout_method") }},
    {{ adapter.quote("is_order_rejected") }},
    {{ adapter.quote("merchant_id") }},
    {{ adapter.quote("invoice_template") }},
    {{ adapter.quote("host") }}

  from source
)

select * from renamed
