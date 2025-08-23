from datetime import datetime
from typing import List, Optional

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class SocialLink(BaseModel):
    created_at: Optional[str] = None
    type: Optional[str] = None
    updated_at: Optional[str] = None
    url: Optional[str] = None


class Balance(BaseModel):
    currency: Optional[str] = None
    value: Optional[float] = None
    value_in_cents: Optional[int] = None


class ActiveRecurringContributions(BaseModel):
    collective_id: Optional[int] = None
    monthly: Optional[int] = None
    monthly_count: Optional[int] = None
    yearly: Optional[int] = None
    yearly_count: Optional[int] = None


class Stats(BaseModel):
    active_recurring_contributions: Optional[ActiveRecurringContributions] = None
    balance: Optional[Balance] = None
    total_amount_received: Optional[Balance] = None


class Location(BaseModel):
    address: Optional[str] = None
    country: Optional[str] = None
    id: Optional[str] = None
    lat: Optional[float] = None
    long: Optional[float] = None
    name: Optional[str] = None
    structured: Optional[str] = None


class EarlyAccess(BaseModel):
    crowdfunding_redesign: Optional[bool] = None
    host_reports: Optional[bool] = None


class Settings(BaseModel):
    early_access: Optional[EarlyAccess] = None


class Features(BaseModel):
    about: Optional[str] = None
    account_management: Optional[str] = None
    agreements: Optional[str] = None
    alipay: Optional[str] = None
    all: Optional[str] = None
    charge_hosting_fees: Optional[str] = None
    chart_of_accounts: Optional[str] = None
    collective_goals: Optional[str] = None
    connected_accounts: Optional[str] = None
    connect_bank_accounts: Optional[str] = None
    contact_collective: Optional[str] = None
    contact_form: Optional[str] = None
    conversations: Optional[str] = None
    create_collective: Optional[str] = None
    email_notifications_panel: Optional[str] = None
    emit_gift_cards: Optional[str] = None
    events: Optional[str] = None
    expected_funds: Optional[str] = None
    expense_security_checks: Optional[str] = None
    funds_grants_management: Optional[str] = None
    host_dashboard: Optional[str] = None
    multi_currency_expenses: Optional[str] = None
    off_platform_transactions: Optional[str] = None
    order: Optional[str] = None
    paypal_donations: Optional[str] = None
    paypal_payouts: Optional[str] = None
    projects: Optional[str] = None
    receive_expenses: Optional[str] = None
    receive_financial_contributions: Optional[str] = None
    receive_host_applications: Optional[str] = None
    recurring_contributions: Optional[str] = None
    request_virtual_cards: Optional[str] = None
    restricted_funds: Optional[str] = None
    stripe_payment_intent: Optional[str] = None
    tax_forms: Optional[str] = None
    team: Optional[str] = None
    top_financial_contributors: Optional[str] = None
    transactions: Optional[str] = None
    transferwise: Optional[str] = None
    updates: Optional[str] = None
    use_expenses: Optional[str] = None
    use_payment_methods: Optional[str] = None
    vendors: Optional[str] = None
    virtual_cards: Optional[str] = None


class CollectiveMinimumAdmins(BaseModel):
    applies: Optional[str] = None
    freeze: Optional[bool] = None
    number_of_admins: Optional[int] = None


class Policies(BaseModel):
    collective_minimum_admins: Optional[CollectiveMinimumAdmins] = None


class AddFunds(BaseModel):
    allowed: Optional[bool] = None
    reason: Optional[str] = None
    reason_details: Optional[str] = None


class Permissions(BaseModel):
    add_funds: Optional[AddFunds] = None


class TransactionReportNode(BaseModel):
    date: Optional[str] = None


class TransactionReports(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    nodes: Optional[List[TransactionReportNode]] = None
    time_unit: Optional[str] = None


# Complex nested structures for parent_account
class ParentAccountFeatures(BaseModel):
    about: Optional[str] = None
    account_management: Optional[str] = None
    agreements: Optional[str] = None
    alipay: Optional[str] = None
    all: Optional[str] = None
    charge_hosting_fees: Optional[str] = None
    chart_of_accounts: Optional[str] = None
    collective_goals: Optional[str] = None
    connected_accounts: Optional[str] = None
    connect_bank_accounts: Optional[str] = None
    contact_collective: Optional[str] = None
    contact_form: Optional[str] = None
    conversations: Optional[str] = None
    create_collective: Optional[str] = None
    email_notifications_panel: Optional[str] = None
    emit_gift_cards: Optional[str] = None
    events: Optional[str] = None
    expected_funds: Optional[str] = None
    expense_security_checks: Optional[str] = None
    funds_grants_management: Optional[str] = None
    host_dashboard: Optional[str] = None
    multi_currency_expenses: Optional[str] = None
    off_platform_transactions: Optional[str] = None
    order: Optional[str] = None
    paypal_donations: Optional[str] = None
    paypal_payouts: Optional[str] = None
    projects: Optional[str] = None
    receive_expenses: Optional[str] = None
    receive_financial_contributions: Optional[str] = None
    receive_host_applications: Optional[str] = None
    recurring_contributions: Optional[str] = None
    request_virtual_cards: Optional[str] = None
    restricted_funds: Optional[str] = None
    stripe_payment_intent: Optional[str] = None
    tax_forms: Optional[str] = None
    team: Optional[str] = None
    top_financial_contributors: Optional[str] = None
    transactions: Optional[str] = None
    transferwise: Optional[str] = None
    updates: Optional[str] = None
    use_expenses: Optional[str] = None
    use_payment_methods: Optional[str] = None
    vendors: Optional[str] = None
    virtual_cards: Optional[str] = None
    id: Optional[str] = None


class VATSettings(BaseModel):
    type: Optional[str] = None


class CollectivePageBackground(BaseModel):
    crop_x: Optional[int] = None
    crop_y: Optional[int] = None
    is_aligned_right: Optional[bool] = None
    media_size_height: Optional[int] = None
    media_size_width: Optional[int] = None
    zoom: Optional[str] = None


class CollectivePage(BaseModel):
    background: Optional[CollectivePageBackground] = None


class ParentAccountSettings(BaseModel):
    vat: Optional[VATSettings] = None
    collective_page: Optional[CollectivePage] = None


class ParentAccountStats(BaseModel):
    active_recurring_contributions: Optional[ActiveRecurringContributions] = None
    contributions_count: Optional[int] = None
    contributors_count: Optional[int] = None
    id: Optional[str] = None


class ParentAccountPolicies(BaseModel):
    collective_admins_can_refund: Optional[str] = None
    collective_admins_can_see_payout_methods: Optional[str] = None
    expense_public_vendors: Optional[str] = None
    require_2fa_for_admins: Optional[str] = None
    id: Optional[str] = None


class ParentAccountPermissions(BaseModel):
    id: Optional[str] = None


class ParentAccount(BaseModel):
    background_image_url: Optional[str] = None
    can_have_changelog_updates: Optional[bool] = None
    categories: Optional[List[str]] = None
    connected_accounts: Optional[str] = None
    created_at: Optional[str] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    duplicated_from_account: Optional[str] = None
    emails: Optional[str] = None
    expense_policy: Optional[str] = None
    features: Optional[ParentAccountFeatures] = None
    github_handle: Optional[str] = None
    id: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_archived: Optional[bool] = None
    is_frozen: Optional[bool] = None
    is_host: Optional[bool] = None
    is_incognito: Optional[bool] = None
    is_suspended: Optional[bool] = None
    is_verified: Optional[bool] = None
    legacy_id: Optional[int] = None
    legal_documents: Optional[str] = None
    legal_name: Optional[str] = None
    location: Optional[Location] = None
    long_description: Optional[str] = None
    member_invitations: Optional[str] = None
    name: Optional[str] = None
    parent_account: Optional[str] = None
    payment_methods: Optional[str] = None
    payment_methods_with_pending_confirmation: Optional[str] = None
    payout_methods: Optional[str] = None
    permissions: Optional[ParentAccountPermissions] = None
    policies: Optional[ParentAccountPolicies] = None
    repository_url: Optional[str] = None
    settings: Optional[ParentAccountSettings] = None
    slug: Optional[str] = None
    social_links: Optional[List[SocialLink]] = None
    stats: Optional[ParentAccountStats] = None
    supported_expense_types: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    transaction_reports: Optional[TransactionReports] = None
    transferwise: Optional[str] = None
    twitter_handle: Optional[str] = None
    type: Optional[str] = None
    updated_at: Optional[str] = None
    website: Optional[str] = None


class TransferwiseAvailableCurrency(BaseModel):
    code: Optional[str] = None
    min_invoice_amount: Optional[int] = None


class TransferwiseBalance(BaseModel):
    currency: Optional[str] = None
    value: Optional[float] = None
    value_in_cents: Optional[int] = None


class Transferwise(BaseModel):
    amount_batched: Optional[float] = None
    available_currencies: Optional[List[TransferwiseAvailableCurrency]] = None
    balances: Optional[List[TransferwiseBalance]] = None
    id: Optional[str] = None


class Accounts(BaseModel):
    id: str = Column("VARCHAR")
    legacy_id: int | None = Column("INTEGER")
    slug: str | None = Column("VARCHAR")
    type: str | None = Column("VARCHAR")
    name: str | None = Column("VARCHAR")
    long_description: str | None = Column("VARCHAR")
    social_links: List[SocialLink] | None = Column(
        "ARRAY(ROW(created_at VARCHAR, type VARCHAR, updated_at VARCHAR, url VARCHAR))"
    )
    currency: str | None = Column("VARCHAR")
    expense_policy: str | None = Column("VARCHAR")
    is_verified: bool | None = Column("BOOLEAN")
    is_incognito: bool | None = Column("BOOLEAN")
    image_url: str | None = Column("VARCHAR")
    created_at: datetime | None = Column("TIMESTAMP")
    updated_at: datetime | None = Column("TIMESTAMP")
    is_archived: bool | None = Column("BOOLEAN")
    is_frozen: bool | None = Column("BOOLEAN")
    is_suspended: bool | None = Column("BOOLEAN")
    is_active: bool | None = Column("BOOLEAN")
    is_host: bool | None = Column("BOOLEAN")
    is_admin: bool | None = Column("BOOLEAN")
    settings: Settings | None = Column(
        "ROW(early_access ROW(crowdfunding_redesign BOOLEAN, host_reports BOOLEAN))"
    )
    supported_expense_types: List[str] | None = Column("ARRAY(VARCHAR)")
    categories: List[str] | None = Column("ARRAY(VARCHAR)")
    stats: Stats | None = Column(
        "ROW("
        "active_recurring_contributions ROW("
        "collective_id INTEGER, "
        "monthly INTEGER, "
        "monthly_count INTEGER, "
        "yearly INTEGER, "
        "yearly_count INTEGER"
        "), "
        "balance ROW(currency VARCHAR, value DOUBLE, value_in_cents BIGINT), "
        "total_amount_received ROW("
        "currency VARCHAR, "
        "value DOUBLE, "
        "value_in_cents BIGINT"
        ")"
        ")"
    )
    can_have_changelog_updates: bool | None = Column("BOOLEAN")
    features: Features | None = Column(
        "ROW("
        "about VARCHAR, "
        "account_management VARCHAR, "
        "agreements VARCHAR, "
        "alipay VARCHAR, "
        '"all" VARCHAR, '
        "charge_hosting_fees VARCHAR, "
        "chart_of_accounts VARCHAR, "
        "collective_goals VARCHAR, "
        "connected_accounts VARCHAR, "
        "connect_bank_accounts VARCHAR, "
        "contact_collective VARCHAR, "
        "contact_form VARCHAR, "
        "conversations VARCHAR, "
        "create_collective VARCHAR, "
        "email_notifications_panel VARCHAR, "
        "emit_gift_cards VARCHAR, "
        "events VARCHAR, "
        "expected_funds VARCHAR, "
        "expense_security_checks VARCHAR, "
        "funds_grants_management VARCHAR, "
        "host_dashboard VARCHAR, "
        "multi_currency_expenses VARCHAR, "
        "off_platform_transactions VARCHAR, "
        '"order" VARCHAR, '
        "paypal_donations VARCHAR, "
        "paypal_payouts VARCHAR, "
        "projects VARCHAR, "
        "receive_expenses VARCHAR, "
        "receive_financial_contributions VARCHAR, "
        "receive_host_applications VARCHAR, "
        "recurring_contributions VARCHAR, "
        "request_virtual_cards VARCHAR, "
        "restricted_funds VARCHAR, "
        "stripe_payment_intent VARCHAR, "
        "tax_forms VARCHAR, "
        "team VARCHAR, "
        "top_financial_contributors VARCHAR, "
        "transactions VARCHAR, "
        "transferwise VARCHAR, "
        "updates VARCHAR, "
        "use_expenses VARCHAR, "
        "use_payment_methods VARCHAR, "
        "vendors VARCHAR, "
        "virtual_cards VARCHAR"
        ")"
    )
    policies: Policies | None = Column(
        "ROW("
        "collective_minimum_admins ROW("
        "applies VARCHAR, "
        '"freeze" BOOLEAN, '
        "number_of_admins INTEGER"
        ")"
        ")"
    )
    permissions: Permissions | None = Column(
        "ROW(add_funds ROW(allowed BOOLEAN, reason VARCHAR, reason_details VARCHAR))"
    )
    transaction_reports: TransactionReports | None = Column(
        "ROW("
        "date_from VARCHAR, "
        "date_to VARCHAR, "
        "nodes ARRAY(ROW(date VARCHAR)), "
        "time_unit VARCHAR"
        ")"
    )
    description: str | None = Column("VARCHAR")
    website: str | None = Column("VARCHAR")
    background_image_url: str | None = Column("VARCHAR")
    tags: List[str] | None = Column("ARRAY(VARCHAR)")
    github_handle: str | None = Column("VARCHAR")
    repository_url: str | None = Column("VARCHAR")
    location: Location | None = Column(
        "ROW("
        "address VARCHAR, "
        "country VARCHAR, "
        "id VARCHAR, "
        "lat DOUBLE, "
        "long DOUBLE, "
        "name VARCHAR, "
        "structured VARCHAR"
        ")"
    )
    parent_account: ParentAccount | None = Column(
        "ROW("
        "background_image_url VARCHAR, "
        "can_have_changelog_updates BOOLEAN, "
        "categories ARRAY(VARCHAR), "
        "connected_accounts VARCHAR, "
        "created_at VARCHAR, "
        "currency VARCHAR, "
        "description VARCHAR, "
        "duplicated_from_account VARCHAR, "
        "emails VARCHAR, "
        "expense_policy VARCHAR, "
        "features ROW("
        "about VARCHAR, "
        "account_management VARCHAR, "
        "agreements VARCHAR, "
        "alipay VARCHAR, "
        '"all" VARCHAR, '
        "charge_hosting_fees VARCHAR, "
        "chart_of_accounts VARCHAR, "
        "collective_goals VARCHAR, "
        "connected_accounts VARCHAR, "
        "connect_bank_accounts VARCHAR, "
        "contact_collective VARCHAR, "
        "contact_form VARCHAR, "
        "conversations VARCHAR, "
        "create_collective VARCHAR, "
        "email_notifications_panel VARCHAR, "
        "emit_gift_cards VARCHAR, "
        "events VARCHAR, "
        "expected_funds VARCHAR, "
        "expense_security_checks VARCHAR, "
        "funds_grants_management VARCHAR, "
        "host_dashboard VARCHAR, "
        "multi_currency_expenses VARCHAR, "
        "off_platform_transactions VARCHAR, "
        '"order" VARCHAR, '
        "paypal_donations VARCHAR, "
        "paypal_payouts VARCHAR, "
        "projects VARCHAR, "
        "receive_expenses VARCHAR, "
        "receive_financial_contributions VARCHAR, "
        "receive_host_applications VARCHAR, "
        "recurring_contributions VARCHAR, "
        "request_virtual_cards VARCHAR, "
        "restricted_funds VARCHAR, "
        "stripe_payment_intent VARCHAR, "
        "tax_forms VARCHAR, "
        "team VARCHAR, "
        "top_financial_contributors VARCHAR, "
        "transactions VARCHAR, "
        "transferwise VARCHAR, "
        "updates VARCHAR, "
        "use_expenses VARCHAR, "
        "use_payment_methods VARCHAR, "
        "vendors VARCHAR, "
        "virtual_cards VARCHAR, "
        "id VARCHAR"
        "), "
        "github_handle VARCHAR, "
        "id VARCHAR, "
        "image_url VARCHAR, "
        "is_active BOOLEAN, "
        "is_admin BOOLEAN, "
        "is_archived BOOLEAN, "
        "is_frozen BOOLEAN, "
        "is_host BOOLEAN, "
        "is_incognito BOOLEAN, "
        "is_suspended BOOLEAN, "
        "is_verified BOOLEAN, "
        "legacy_id INTEGER, "
        "legal_documents VARCHAR, "
        "legal_name VARCHAR, "
        "location ROW("
        "address VARCHAR, "
        "country VARCHAR, "
        "id VARCHAR, "
        "lat DOUBLE, "
        "long DOUBLE, "
        "name VARCHAR, "
        "structured VARCHAR"
        "), "
        "long_description VARCHAR, "
        "member_invitations VARCHAR, "
        "name VARCHAR, "
        "parent_account VARCHAR, "
        "payment_methods VARCHAR, "
        "payment_methods_with_pending_confirmation VARCHAR, "
        "payout_methods VARCHAR, "
        "permissions ROW(id VARCHAR), "
        "policies ROW("
        "collective_admins_can_refund VARCHAR, "
        "collective_admins_can_see_payout_methods VARCHAR, "
        "expense_public_vendors VARCHAR, "
        "require_2fa_for_admins VARCHAR, "
        "id VARCHAR"
        "), "
        "repository_url VARCHAR, "
        "settings ROW("
        "vat ROW(type VARCHAR), "
        "collective_page ROW("
        "background ROW("
        "crop_x INTEGER, "
        "crop_y INTEGER, "
        "is_aligned_right BOOLEAN, "
        "media_size_height INTEGER, "
        "media_size_width INTEGER, "
        "zoom VARCHAR"
        ")"
        ")"
        "), "
        "slug VARCHAR, "
        "social_links ARRAY("
        "ROW(created_at VARCHAR, type VARCHAR, updated_at VARCHAR, url VARCHAR)"
        "), "
        "stats ROW("
        "active_recurring_contributions ROW("
        "collective_id INTEGER, "
        "monthly INTEGER, "
        "monthly_count INTEGER, "
        "yearly INTEGER, "
        "yearly_count INTEGER"
        "), "
        "contributions_count INTEGER, "
        "contributors_count INTEGER, "
        "id VARCHAR"
        "), "
        "supported_expense_types ARRAY(VARCHAR), "
        "tags ARRAY(VARCHAR), "
        "transaction_reports ROW("
        "date_from VARCHAR, "
        "date_to VARCHAR, "
        "nodes ARRAY(ROW(date VARCHAR)), "
        "time_unit VARCHAR"
        "), "
        "transferwise VARCHAR, "
        "twitter_handle VARCHAR, "
        "type VARCHAR, "
        "updated_at VARCHAR, "
        "website VARCHAR"
        ")"
    )
    twitter_handle: str | None = Column("VARCHAR")
    transferwise: Transferwise | None = Column(
        "ROW("
        "amount_batched DOUBLE, "
        "available_currencies ARRAY("
        "ROW(code VARCHAR, min_invoice_amount INTEGER)"
        "), "
        "balances ARRAY("
        "ROW(currency VARCHAR, value DOUBLE, value_in_cents BIGINT)"
        "), "
        "id VARCHAR"
        ")"
    )
    member_invitations: List[str] | None = Column("ARRAY(VARCHAR)")
    legal_documents: List[str] | None = Column("ARRAY(VARCHAR)")
    emails: List[str] | None = Column("ARRAY(VARCHAR)")
    payout_methods: List[str] | None = Column("ARRAY(VARCHAR)")
    payment_methods: List[str] | None = Column("ARRAY(VARCHAR)")
    payment_methods_with_pending_confirmation: List[str] | None = Column(
        "ARRAY(VARCHAR)"
    )
    connected_accounts: List[str] | None = Column("ARRAY(VARCHAR)")
    dlt_load_id: str = Column("VARCHAR", column_name="_dlt_load_id")
    dlt_id: str = Column("VARCHAR", column_name="_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="open_collective",
    table="accounts",
    base=Accounts,
    rows=[
        Accounts(
            id="eeng0kzd-yvor4pzn-dgpbma83-7xlw95jl",
            legacy_id=9701,
            slug="big-nerd-ranch",
            type="INDIVIDUAL",
            name="Big Nerd Ranch",
            long_description=None,
            social_links=[],
            currency="USD",
            expense_policy="",
            is_verified=False,
            is_incognito=False,
            image_url="https://images.opencollective.com/big-nerd-ranch/avatar.png",
            created_at=datetime(2025, 8, 19, 19, 56, 13, 52000),
            updated_at=datetime(2025, 8, 19, 17, 17, 8, 16000),
            is_archived=False,
            is_frozen=False,
            is_suspended=False,
            is_active=False,
            is_host=False,
            is_admin=False,
            settings=Settings(
                early_access=EarlyAccess(
                    crowdfunding_redesign=False, host_reports=False
                )
            ),
            supported_expense_types=["INVOICE", "RECEIPT"],
            categories=[],
            stats=Stats(
                active_recurring_contributions=ActiveRecurringContributions(
                    collective_id=9701,
                    monthly=0,
                    monthly_count=0,
                    yearly=0,
                    yearly_count=0,
                ),
                balance=Balance(currency="USD", value=0, value_in_cents=0),
                total_amount_received=Balance(
                    currency="USD", value=0, value_in_cents=0
                ),
            ),
            can_have_changelog_updates=False,
            features=Features(
                about="AVAILABLE",
                account_management="ACTIVE",
                agreements="",
                alipay="",
                all="",
                charge_hosting_fees="",
                chart_of_accounts="",
                collective_goals="",
                connected_accounts="",
                connect_bank_accounts="",
                contact_collective="",
                contact_form="",
                conversations="",
                create_collective="",
                email_notifications_panel="",
                emit_gift_cards="",
                events="",
                expected_funds="",
                expense_security_checks="",
                funds_grants_management="",
                host_dashboard="",
                multi_currency_expenses="",
                off_platform_transactions="",
                order="ACTIVE",
                paypal_donations="",
                paypal_payouts="",
                projects="",
                receive_expenses="",
                receive_financial_contributions="",
                receive_host_applications="",
                recurring_contributions="",
                request_virtual_cards="",
                restricted_funds="",
                stripe_payment_intent="",
                tax_forms="",
                team="",
                top_financial_contributors="",
                transactions="",
                transferwise="",
                updates="",
                use_expenses="",
                use_payment_methods="",
                vendors="",
                virtual_cards="",
            ),
            policies=Policies(
                collective_minimum_admins=CollectiveMinimumAdmins(
                    applies="NEW_COLLECTIVES", freeze=False, number_of_admins=0
                )
            ),
            permissions=Permissions(
                add_funds=AddFunds(allowed=False, reason="", reason_details="")
            ),
            transaction_reports=TransactionReports(
                date_from="", date_to="", nodes=[], time_unit="MONTH"
            ),
            description=None,
            website=None,
            background_image_url=None,
            tags=None,
            github_handle=None,
            repository_url=None,
            location=Location(
                address="", country="", id="", lat=0.0, long=0.0, name="", structured=""
            ),
            parent_account=None,
            twitter_handle=None,
            transferwise=None,
            member_invitations=None,
            legal_documents=None,
            emails=None,
            payout_methods=None,
            payment_methods=None,
            payment_methods_with_pending_confirmation=None,
            connected_accounts=None,
            dlt_load_id="1755719508.455616",
            dlt_id="geEdKazutWlwVQ",
        ),
        Accounts(
            id="eeng0kzd-yvor4pzv-lrqbma83-7xlw95jl",
            legacy_id=4401,
            slug="bignerdranch",
            type="ORGANIZATION",
            name="Big Nerd Ranch",
            long_description="<p>Big Nerd Ranch specializes in developing and designing innovative applications for clients around the world. We work with companies of all types, from startups to nonprofits to large enterprise clients.</p>",
            social_links=[
                SocialLink(
                    created_at="2023-01-06T12:16:03.418Z",
                    type="WEBSITE",
                    updated_at="2023-01-06T12:16:03.418Z",
                    url="https://bignerdranch.com",
                )
            ],
            currency="USD",
            expense_policy="",
            is_verified=False,
            is_incognito=False,
            image_url="https://images.opencollective.com/bignerdranch/c75de62/logo.png",
            created_at=datetime(2025, 8, 20, 19, 56, 13, 52000),
            updated_at=datetime(2025, 8, 20, 19, 56, 13, 52000),
            is_archived=False,
            is_frozen=False,
            is_suspended=False,
            is_active=False,
            is_host=False,
            is_admin=False,
            settings=Settings(
                early_access=EarlyAccess(
                    crowdfunding_redesign=False, host_reports=False
                )
            ),
            supported_expense_types=["INVOICE", "RECEIPT"],
            categories=[],
            stats=Stats(
                active_recurring_contributions=ActiveRecurringContributions(
                    collective_id=4401,
                    monthly=0,
                    monthly_count=0,
                    yearly=0,
                    yearly_count=0,
                ),
                balance=Balance(currency="USD", value=-2775.73, value_in_cents=-277573),
                total_amount_received=Balance(
                    currency="USD", value=0, value_in_cents=0
                ),
            ),
            can_have_changelog_updates=False,
            features=Features(
                about="ACTIVE",
                account_management="ACTIVE",
                agreements="",
                alipay="",
                all="",
                charge_hosting_fees="",
                chart_of_accounts="",
                collective_goals="",
                connected_accounts="",
                connect_bank_accounts="",
                contact_collective="",
                contact_form="",
                conversations="",
                create_collective="",
                email_notifications_panel="",
                emit_gift_cards="",
                events="",
                expected_funds="",
                expense_security_checks="",
                funds_grants_management="",
                host_dashboard="",
                multi_currency_expenses="",
                off_platform_transactions="",
                order="",
                paypal_donations="",
                paypal_payouts="",
                projects="",
                receive_expenses="AVAILABLE",
                receive_financial_contributions="",
                receive_host_applications="",
                recurring_contributions="",
                request_virtual_cards="",
                restricted_funds="",
                stripe_payment_intent="",
                tax_forms="",
                team="ACTIVE",
                top_financial_contributors="",
                transactions="",
                transferwise="",
                updates="",
                use_expenses="",
                use_payment_methods="",
                vendors="",
                virtual_cards="",
            ),
            policies=Policies(
                collective_minimum_admins=CollectiveMinimumAdmins(
                    applies="NEW_COLLECTIVES", freeze=False, number_of_admins=0
                )
            ),
            permissions=Permissions(
                add_funds=AddFunds(allowed=False, reason="", reason_details="")
            ),
            transaction_reports=TransactionReports(
                date_from="",
                date_to="",
                nodes=[
                    TransactionReportNode(date="2025-08-01T00:00:00.000Z"),
                    TransactionReportNode(date="2025-07-01T00:00:00.000Z"),
                ],
                time_unit="MONTH",
            ),
            description="App Development & Training Since 2001",
            website="https://bignerdranch.com",
            background_image_url=None,
            tags=["user"],
            github_handle=None,
            repository_url=None,
            location=Location(
                address="", country="", id="", lat=0.0, long=0.0, name="", structured=""
            ),
            parent_account=None,
            twitter_handle=None,
            transferwise=None,
            member_invitations=None,
            legal_documents=None,
            emails=None,
            payout_methods=None,
            payment_methods=None,
            payment_methods_with_pending_confirmation=None,
            connected_accounts=None,
            dlt_load_id="1755719508.455616",
            dlt_id="oxYwVPRWlBNI0g",
        ),
        Accounts(
            id="3z8arxve-ymko60y4-l9wqgl5n-bj9w704d",
            legacy_id=615555,
            slug="chris-b",
            type="INDIVIDUAL",
            name="Chris B",
            long_description=None,
            social_links=[],
            currency="USD",
            expense_policy="",
            is_verified=False,
            is_incognito=False,
            image_url="https://images.opencollective.com/chris-b/avatar.png",
            created_at=datetime(2025, 8, 21, 23, 54, 15, 454000),
            updated_at=datetime(2025, 8, 21, 13, 55, 54, 981000),
            is_archived=False,
            is_frozen=False,
            is_suspended=False,
            is_active=False,
            is_host=False,
            is_admin=False,
            settings=Settings(
                early_access=EarlyAccess(crowdfunding_redesign=True, host_reports=True)
            ),
            supported_expense_types=["INVOICE", "RECEIPT"],
            categories=[],
            stats=Stats(
                active_recurring_contributions=ActiveRecurringContributions(
                    collective_id=615555,
                    monthly=0,
                    monthly_count=0,
                    yearly=0,
                    yearly_count=0,
                ),
                balance=Balance(currency="USD", value=-234.65, value_in_cents=-23465),
                total_amount_received=Balance(
                    currency="USD", value=0, value_in_cents=0
                ),
            ),
            can_have_changelog_updates=False,
            features=Features(
                about="AVAILABLE",
                account_management="ACTIVE",
                agreements="",
                alipay="",
                all="",
                charge_hosting_fees="",
                chart_of_accounts="",
                collective_goals="",
                connected_accounts="",
                connect_bank_accounts="",
                contact_collective="",
                contact_form="",
                conversations="",
                create_collective="",
                email_notifications_panel="",
                emit_gift_cards="",
                events="",
                expected_funds="",
                expense_security_checks="",
                funds_grants_management="",
                host_dashboard="",
                multi_currency_expenses="",
                off_platform_transactions="",
                order="",
                paypal_donations="",
                paypal_payouts="",
                projects="",
                receive_expenses="",
                receive_financial_contributions="",
                receive_host_applications="",
                recurring_contributions="ACTIVE",
                request_virtual_cards="",
                restricted_funds="",
                stripe_payment_intent="",
                tax_forms="",
                team="",
                top_financial_contributors="",
                transactions="ACTIVE",
                transferwise="",
                updates="",
                use_expenses="",
                use_payment_methods="",
                vendors="",
                virtual_cards="",
            ),
            policies=Policies(
                collective_minimum_admins=CollectiveMinimumAdmins(
                    applies="NEW_COLLECTIVES", freeze=False, number_of_admins=0
                )
            ),
            permissions=Permissions(
                add_funds=AddFunds(allowed=False, reason="", reason_details="")
            ),
            transaction_reports=TransactionReports(
                date_from="",
                date_to="",
                nodes=[
                    TransactionReportNode(date="2025-08-01T00:00:00.000Z"),
                    TransactionReportNode(date="2025-07-01T00:00:00.000Z"),
                ],
                time_unit="MONTH",
            ),
            description=None,
            website=None,
            background_image_url=None,
            tags=None,
            github_handle=None,
            repository_url=None,
            location=Location(
                address="", country="", id="", lat=0.0, long=0.0, name="", structured=""
            ),
            parent_account=None,
            twitter_handle=None,
            transferwise=None,
            member_invitations=None,
            legal_documents=None,
            emails=None,
            payout_methods=None,
            payment_methods=None,
            payment_methods_with_pending_confirmation=None,
            connected_accounts=None,
            dlt_load_id="1755719508.455616",
            dlt_id="cEwdTpUcj332Aw",
        ),
    ],
)
