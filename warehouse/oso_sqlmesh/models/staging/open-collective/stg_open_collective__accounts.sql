MODEL (
  name oso.stg_open_collective__accounts,
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column created_at,
    batch_size 365,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  partitioned_by (DAY("created_at")),
  start '2015-01-01',
  cron '@daily',
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  ignored_rules (
    "incrementalmustdefinenogapsaudit",
  ),
  tags (
    "incremental"
  ),
  enabled false
);

SELECT
  id,
  legacy_id,
  slug,
  type,
  name,
  long_description,
  CAST(social_links AS ARRAY(ROW(
    created_at VARCHAR,
    type VARCHAR,
    updated_at VARCHAR,
    url VARCHAR
  ))) AS social_links,
  currency,
  expense_policy,
  is_verified,
  is_incognito,
  image_url,
  created_at,
  updated_at,
  is_archived,
  is_frozen,
  is_suspended,
  is_active,
  is_host,
  is_admin,
  CAST(settings AS ROW(
    early_access ROW(
      crowdfunding_redesign BOOLEAN,
      host_reports BOOLEAN
    )
  )) AS settings,
  CAST(supported_expense_types AS ARRAY(VARCHAR)) AS
    supported_expense_types,
  CAST(categories AS ARRAY(VARCHAR)) AS categories,
  CAST(stats AS ROW(
    active_recurring_contributions ROW(
      collective_id INTEGER,
      monthly INTEGER,
      monthly_count INTEGER,
      yearly INTEGER,
      yearly_count INTEGER
    ),
    balance ROW(
      currency VARCHAR,
      value DOUBLE,
      value_in_cents BIGINT
    ),
    total_amount_received ROW(
      currency VARCHAR,
      value DOUBLE,
      value_in_cents BIGINT
    )
  )) AS stats,
  can_have_changelog_updates,
  CAST(features AS ROW(
    about VARCHAR,
    account_management VARCHAR,
    agreements VARCHAR,
    alipay VARCHAR,
    all VARCHAR,
    charge_hosting_fees VARCHAR,
    chart_of_accounts VARCHAR,
    collective_goals VARCHAR,
    connected_accounts VARCHAR,
    connect_bank_accounts VARCHAR,
    contact_collective VARCHAR,
    contact_form VARCHAR,
    conversations VARCHAR,
    create_collective VARCHAR,
    email_notifications_panel VARCHAR,
    emit_gift_cards VARCHAR,
    events VARCHAR,
    expected_funds VARCHAR,
    expense_security_checks VARCHAR,
    funds_grants_management VARCHAR,
    host_dashboard VARCHAR,
    multi_currency_expenses VARCHAR,
    off_platform_transactions VARCHAR,
    order VARCHAR,
    paypal_donations VARCHAR,
    paypal_payouts VARCHAR,
    projects VARCHAR,
    receive_expenses VARCHAR,
    receive_financial_contributions VARCHAR,
    receive_host_applications VARCHAR,
    recurring_contributions VARCHAR,
    request_virtual_cards VARCHAR,
    restricted_funds VARCHAR,
    stripe_payment_intent VARCHAR,
    tax_forms VARCHAR,
    team VARCHAR,
    top_financial_contributors VARCHAR,
    transactions VARCHAR,
    transferwise VARCHAR,
    updates VARCHAR,
    use_expenses VARCHAR,
    use_payment_methods VARCHAR,
    vendors VARCHAR,
    virtual_cards VARCHAR
  )) AS features,
  CAST(policies AS ROW(
    collective_minimum_admins ROW(
      applies VARCHAR,
      freeze BOOLEAN,
      number_of_admins INTEGER
    )
  )) AS policies,
  CAST(permissions AS ROW(
    add_funds ROW(
      allowed BOOLEAN,
      reason VARCHAR,
      reason_details VARCHAR
    )
  )) AS permissions,
  CAST(transaction_reports AS ROW(
    date_from VARCHAR,
    date_to VARCHAR,
    nodes ARRAY(ROW(date VARCHAR)),
    time_unit VARCHAR
  )) AS transaction_reports,
  _dlt_load_id,
  _dlt_id,
  description,
  website,
  background_image_url,
  CAST(tags AS ARRAY(VARCHAR)) AS tags,
  github_handle,
  repository_url,
  CAST(location AS ROW(
    address VARCHAR,
    country VARCHAR,
    id VARCHAR,
    lat DOUBLE,
    long DOUBLE,
    name VARCHAR,
    structured VARCHAR
  )) AS location,
  CAST(parent_account AS ROW(
    background_image_url VARCHAR,
    can_have_changelog_updates BOOLEAN,
    categories ARRAY(VARCHAR),
    connected_accounts VARCHAR,
    created_at VARCHAR,
    currency VARCHAR,
    description VARCHAR,
    duplicated_from_account VARCHAR,
    emails VARCHAR,
    expense_policy VARCHAR,
    features ROW(
      about VARCHAR,
      account_management VARCHAR,
      agreements VARCHAR,
      alipay VARCHAR,
      all VARCHAR,
      charge_hosting_fees VARCHAR,
      chart_of_accounts VARCHAR,
      collective_goals VARCHAR,
      connected_accounts VARCHAR,
      connect_bank_accounts VARCHAR,
      contact_collective VARCHAR,
      contact_form VARCHAR,
      conversations VARCHAR,
      create_collective VARCHAR,
      email_notifications_panel VARCHAR,
      emit_gift_cards VARCHAR,
      events VARCHAR,
      expected_funds VARCHAR,
      expense_security_checks VARCHAR,
      funds_grants_management VARCHAR,
      host_dashboard VARCHAR,
      multi_currency_expenses VARCHAR,
      off_platform_transactions VARCHAR,
      order VARCHAR,
      paypal_donations VARCHAR,
      paypal_payouts VARCHAR,
      projects VARCHAR,
      receive_expenses VARCHAR,
      receive_financial_contributions VARCHAR,
      receive_host_applications VARCHAR,
      recurring_contributions VARCHAR,
      request_virtual_cards VARCHAR,
      restricted_funds VARCHAR,
      stripe_payment_intent VARCHAR,
      tax_forms VARCHAR,
      team VARCHAR,
      top_financial_contributors VARCHAR,
      transactions VARCHAR,
      transferwise VARCHAR,
      updates VARCHAR,
      use_expenses VARCHAR,
      use_payment_methods VARCHAR,
      vendors VARCHAR,
      virtual_cards VARCHAR,
      id VARCHAR
    ),
    github_handle VARCHAR,
    id VARCHAR,
    image_url VARCHAR,
    is_active BOOLEAN,
    is_admin BOOLEAN,
    is_archived BOOLEAN,
    is_frozen BOOLEAN,
    is_host BOOLEAN,
    is_incognito BOOLEAN,
    is_suspended BOOLEAN,
    is_verified BOOLEAN,
    legacy_id INTEGER,
    legal_documents VARCHAR,
    legal_name VARCHAR,
    location ROW(
      address VARCHAR,
      country VARCHAR,
      id VARCHAR,
      lat DOUBLE,
      long DOUBLE,
      name VARCHAR,
      structured VARCHAR
    ),
    long_description VARCHAR,
    member_invitations VARCHAR,
    name VARCHAR,
    parent_account VARCHAR,
    payment_methods VARCHAR,
    payment_methods_with_pending_confirmation VARCHAR,
    payout_methods VARCHAR,
    permissions ROW(id VARCHAR),
    policies ROW(
      collective_admins_can_refund VARCHAR,
      collective_admins_can_see_payout_methods VARCHAR,
      expense_public_vendors VARCHAR,
      require_2fa_for_admins VARCHAR,
      id VARCHAR
    ),
    repository_url VARCHAR,
    settings ROW(
      vat ROW(type VARCHAR),
      collective_page ROW(
        background ROW(
          crop_x INTEGER,
          crop_y INTEGER,
          is_aligned_right BOOLEAN,
          media_size_height INTEGER,
          media_size_width INTEGER,
          zoom VARCHAR
        )
      )
    ),
    slug VARCHAR,
    social_links ARRAY(ROW(
      created_at VARCHAR,
      type VARCHAR,
      updated_at VARCHAR,
      url VARCHAR
    )),
    stats ROW(
      active_recurring_contributions ROW(
        collective_id INTEGER,
        monthly INTEGER,
        monthly_count INTEGER,
        yearly INTEGER,
        yearly_count INTEGER
      ),
      contributions_count INTEGER,
      contributors_count INTEGER,
      id VARCHAR
    ),
    supported_expense_types ARRAY(VARCHAR),
    tags ARRAY(VARCHAR),
    transaction_reports ROW(
      date_from VARCHAR,
      date_to VARCHAR,
      nodes ARRAY(ROW(date VARCHAR)),
      time_unit VARCHAR
    ),
    transferwise VARCHAR,
    twitter_handle VARCHAR,
    type VARCHAR,
    updated_at VARCHAR,
    website VARCHAR
  )) AS parent_account,
  twitter_handle,
  CAST(transferwise AS ROW(
    amount_batched DOUBLE,
    available_currencies ARRAY(ROW(
      code VARCHAR,
      min_invoice_amount INTEGER
    )),
    balances ARRAY(ROW(
      currency VARCHAR,
      value DOUBLE,
      value_in_cents BIGINT
    )),
    id VARCHAR
  )) AS transferwise,
  CAST(member_invitations AS ARRAY(VARCHAR)) AS member_invitations,
  CAST(legal_documents AS ARRAY(VARCHAR)) AS legal_documents,
  CAST(emails AS ARRAY(VARCHAR)) AS emails,
  CAST(payout_methods AS ARRAY(VARCHAR)) AS payout_methods,
  CAST(payment_methods AS ARRAY(VARCHAR)) AS payment_methods,
  CAST(payment_methods_with_pending_confirmation AS ARRAY(VARCHAR)) AS
    payment_methods_with_pending_confirmation,
  CAST(connected_accounts AS ARRAY(VARCHAR)) AS connected_accounts
FROM @oso_source('bigquery.open_collective.accounts')