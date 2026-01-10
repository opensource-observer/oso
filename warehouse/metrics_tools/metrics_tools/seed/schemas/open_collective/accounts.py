from datetime import datetime
from typing import List, Optional

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class SocialLink(BaseModel):
    created_at: Optional[str] = Column("VARCHAR")
    type: Optional[str] = Column("VARCHAR")
    updated_at: Optional[str] = Column("VARCHAR")
    url: Optional[str] = Column("VARCHAR")


class Balance(BaseModel):
    currency: Optional[str] = Column("VARCHAR")
    value: Optional[float] = Column("DOUBLE")
    value_in_cents: Optional[int] = Column("BIGINT")


class ActiveRecurringContributions(BaseModel):
    collective_id: Optional[int] = Column("INTEGER")
    monthly: Optional[int] = Column("INTEGER")
    monthly_count: Optional[int] = Column("INTEGER")
    yearly: Optional[int] = Column("INTEGER")
    yearly_count: Optional[int] = Column("INTEGER")


class Stats(BaseModel):
    active_recurring_contributions: Optional[ActiveRecurringContributions] = Column(
        "ROW(?)"
    )
    balance: Optional[Balance] = Column("ROW(?)")
    total_amount_received: Optional[Balance] = Column("ROW(?)")


class Location(BaseModel):
    address: Optional[str] = Column("VARCHAR")
    country: Optional[str] = Column("VARCHAR")
    id: Optional[str] = Column("VARCHAR")
    lat: Optional[float] = Column("DOUBLE")
    long: Optional[float] = Column("DOUBLE")
    name: Optional[str] = Column("VARCHAR")
    structured: Optional[str] = Column("VARCHAR")


class EarlyAccess(BaseModel):
    crowdfunding_redesign: Optional[bool] = Column("BOOLEAN")
    host_reports: Optional[bool] = Column("BOOLEAN")


class Settings(BaseModel):
    early_access: Optional[EarlyAccess] = Column("ROW(?)")


class Features(BaseModel):
    about: Optional[str] = Column("VARCHAR")
    account_management: Optional[str] = Column("VARCHAR")
    agreements: Optional[str] = Column("VARCHAR")
    alipay: Optional[str] = Column("VARCHAR")
    all: Optional[str] = Column("VARCHAR")
    charge_hosting_fees: Optional[str] = Column("VARCHAR")
    chart_of_accounts: Optional[str] = Column("VARCHAR")
    collective_goals: Optional[str] = Column("VARCHAR")
    connected_accounts: Optional[str] = Column("VARCHAR")
    connect_bank_accounts: Optional[str] = Column("VARCHAR")
    contact_collective: Optional[str] = Column("VARCHAR")
    contact_form: Optional[str] = Column("VARCHAR")
    conversations: Optional[str] = Column("VARCHAR")
    create_collective: Optional[str] = Column("VARCHAR")
    email_notifications_panel: Optional[str] = Column("VARCHAR")
    emit_gift_cards: Optional[str] = Column("VARCHAR")
    events: Optional[str] = Column("VARCHAR")
    expected_funds: Optional[str] = Column("VARCHAR")
    expense_security_checks: Optional[str] = Column("VARCHAR")
    funds_grants_management: Optional[str] = Column("VARCHAR")
    host_dashboard: Optional[str] = Column("VARCHAR")
    multi_currency_expenses: Optional[str] = Column("VARCHAR")
    off_platform_transactions: Optional[str] = Column("VARCHAR")
    order: Optional[str] = Column("VARCHAR")
    paypal_donations: Optional[str] = Column("VARCHAR")
    paypal_payouts: Optional[str] = Column("VARCHAR")
    projects: Optional[str] = Column("VARCHAR")
    receive_expenses: Optional[str] = Column("VARCHAR")
    receive_financial_contributions: Optional[str] = Column("VARCHAR")
    receive_host_applications: Optional[str] = Column("VARCHAR")
    recurring_contributions: Optional[str] = Column("VARCHAR")
    request_virtual_cards: Optional[str] = Column("VARCHAR")
    restricted_funds: Optional[str] = Column("VARCHAR")
    stripe_payment_intent: Optional[str] = Column("VARCHAR")
    tax_forms: Optional[str] = Column("VARCHAR")
    team: Optional[str] = Column("VARCHAR")
    top_financial_contributors: Optional[str] = Column("VARCHAR")
    transactions: Optional[str] = Column("VARCHAR")
    transferwise: Optional[str] = Column("VARCHAR")
    updates: Optional[str] = Column("VARCHAR")
    use_expenses: Optional[str] = Column("VARCHAR")
    use_payment_methods: Optional[str] = Column("VARCHAR")
    vendors: Optional[str] = Column("VARCHAR")
    virtual_cards: Optional[str] = Column("VARCHAR")


class CollectiveMinimumAdmins(BaseModel):
    applies: Optional[str] = Column("VARCHAR")
    freeze: Optional[bool] = Column("BOOLEAN")
    number_of_admins: Optional[int] = Column("INTEGER")


class Policies(BaseModel):
    collective_minimum_admins: Optional[CollectiveMinimumAdmins] = Column("ROW(?)")


class AddFunds(BaseModel):
    allowed: Optional[bool] = Column("BOOLEAN")
    reason: Optional[str] = Column("VARCHAR")
    reason_details: Optional[str] = Column("VARCHAR")


class Permissions(BaseModel):
    add_funds: Optional[AddFunds] = Column("ROW(?)")


class TransactionReportNode(BaseModel):
    date: Optional[str] = Column("VARCHAR")


class TransactionReports(BaseModel):
    date_from: Optional[str] = Column("VARCHAR")
    date_to: Optional[str] = Column("VARCHAR")
    nodes: Optional[List[TransactionReportNode]] = Column("ARRAY(ROW(?))")
    time_unit: Optional[str] = Column("VARCHAR")


class ParentAccountFeatures(BaseModel):
    about: Optional[str] = Column("VARCHAR")
    account_management: Optional[str] = Column("VARCHAR")
    agreements: Optional[str] = Column("VARCHAR")
    alipay: Optional[str] = Column("VARCHAR")
    all: Optional[str] = Column("VARCHAR")
    charge_hosting_fees: Optional[str] = Column("VARCHAR")
    chart_of_accounts: Optional[str] = Column("VARCHAR")
    collective_goals: Optional[str] = Column("VARCHAR")
    connected_accounts: Optional[str] = Column("VARCHAR")
    connect_bank_accounts: Optional[str] = Column("VARCHAR")
    contact_collective: Optional[str] = Column("VARCHAR")
    contact_form: Optional[str] = Column("VARCHAR")
    conversations: Optional[str] = Column("VARCHAR")
    create_collective: Optional[str] = Column("VARCHAR")
    email_notifications_panel: Optional[str] = Column("VARCHAR")
    emit_gift_cards: Optional[str] = Column("VARCHAR")
    events: Optional[str] = Column("VARCHAR")
    expected_funds: Optional[str] = Column("VARCHAR")
    expense_security_checks: Optional[str] = Column("VARCHAR")
    funds_grants_management: Optional[str] = Column("VARCHAR")
    host_dashboard: Optional[str] = Column("VARCHAR")
    multi_currency_expenses: Optional[str] = Column("VARCHAR")
    off_platform_transactions: Optional[str] = Column("VARCHAR")
    order: Optional[str] = Column("VARCHAR")
    paypal_donations: Optional[str] = Column("VARCHAR")
    paypal_payouts: Optional[str] = Column("VARCHAR")
    projects: Optional[str] = Column("VARCHAR")
    receive_expenses: Optional[str] = Column("VARCHAR")
    receive_financial_contributions: Optional[str] = Column("VARCHAR")
    receive_host_applications: Optional[str] = Column("VARCHAR")
    recurring_contributions: Optional[str] = Column("VARCHAR")
    request_virtual_cards: Optional[str] = Column("VARCHAR")
    restricted_funds: Optional[str] = Column("VARCHAR")
    stripe_payment_intent: Optional[str] = Column("VARCHAR")
    tax_forms: Optional[str] = Column("VARCHAR")
    team: Optional[str] = Column("VARCHAR")
    top_financial_contributors: Optional[str] = Column("VARCHAR")
    transactions: Optional[str] = Column("VARCHAR")
    transferwise: Optional[str] = Column("VARCHAR")
    updates: Optional[str] = Column("VARCHAR")
    use_expenses: Optional[str] = Column("VARCHAR")
    use_payment_methods: Optional[str] = Column("VARCHAR")
    vendors: Optional[str] = Column("VARCHAR")
    virtual_cards: Optional[str] = Column("VARCHAR")
    id: Optional[str] = Column("VARCHAR")


class VATSettings(BaseModel):
    type: Optional[str] = Column("VARCHAR")


class CollectivePageBackground(BaseModel):
    crop_x: Optional[int] = Column("INTEGER")
    crop_y: Optional[int] = Column("INTEGER")
    is_aligned_right: Optional[bool] = Column("BOOLEAN")
    media_size_height: Optional[int] = Column("INTEGER")
    media_size_width: Optional[int] = Column("INTEGER")
    zoom: Optional[str] = Column("VARCHAR")


class CollectivePage(BaseModel):
    background: Optional[CollectivePageBackground] = Column("ROW(?)")


class ParentAccountSettings(BaseModel):
    vat: Optional[VATSettings] = Column("ROW(?)")
    collective_page: Optional[CollectivePage] = Column("ROW(?)")


class ParentAccountStats(BaseModel):
    active_recurring_contributions: Optional[ActiveRecurringContributions] = Column(
        "ROW(?)"
    )
    contributions_count: Optional[int] = Column("INTEGER")
    contributors_count: Optional[int] = Column("INTEGER")
    id: Optional[str] = Column("VARCHAR")


class ParentAccountPolicies(BaseModel):
    collective_admins_can_refund: Optional[str] = Column("VARCHAR")
    collective_admins_can_see_payout_methods: Optional[str] = Column("VARCHAR")
    expense_public_vendors: Optional[str] = Column("VARCHAR")
    require_2fa_for_admins: Optional[str] = Column("VARCHAR")
    id: Optional[str] = Column("VARCHAR")


class ParentAccountPermissions(BaseModel):
    id: Optional[str] = Column("VARCHAR")


class ParentAccount(BaseModel):
    background_image_url: Optional[str] = Column("VARCHAR")
    can_have_changelog_updates: Optional[bool] = Column("BOOLEAN")
    categories: Optional[List[str]] = Column("ARRAY(VARCHAR)")
    connected_accounts: Optional[str] = Column("VARCHAR")
    created_at: Optional[str] = Column("VARCHAR")
    currency: Optional[str] = Column("VARCHAR")
    description: Optional[str] = Column("VARCHAR")
    duplicated_from_account: Optional[str] = Column("VARCHAR")
    emails: Optional[str] = Column("VARCHAR")
    expense_policy: Optional[str] = Column("VARCHAR")
    features: Optional[ParentAccountFeatures] = Column("ROW(?)")
    github_handle: Optional[str] = Column("VARCHAR")
    id: Optional[str] = Column("VARCHAR")
    image_url: Optional[str] = Column("VARCHAR")
    is_active: Optional[bool] = Column("BOOLEAN")
    is_admin: Optional[bool] = Column("BOOLEAN")
    is_archived: Optional[bool] = Column("BOOLEAN")
    is_frozen: Optional[bool] = Column("BOOLEAN")
    is_host: Optional[bool] = Column("BOOLEAN")
    is_incognito: Optional[bool] = Column("BOOLEAN")
    is_suspended: Optional[bool] = Column("BOOLEAN")
    is_verified: Optional[bool] = Column("BOOLEAN")
    legacy_id: Optional[int] = Column("INTEGER")
    legal_documents: Optional[str] = Column("VARCHAR")
    legal_name: Optional[str] = Column("VARCHAR")
    location: Optional[Location] = Column("ROW(?)")
    long_description: Optional[str] = Column("VARCHAR")
    member_invitations: Optional[str] = Column("VARCHAR")
    name: Optional[str] = Column("VARCHAR")
    parent_account: Optional[str] = Column("VARCHAR")
    payment_methods: Optional[str] = Column("VARCHAR")
    payment_methods_with_pending_confirmation: Optional[str] = Column("VARCHAR")
    payout_methods: Optional[str] = Column("VARCHAR")
    permissions: Optional[ParentAccountPermissions] = Column("ROW(?)")
    policies: Optional[ParentAccountPolicies] = Column("ROW(?)")
    repository_url: Optional[str] = Column("VARCHAR")
    settings: Optional[ParentAccountSettings] = Column("ROW(?)")
    slug: Optional[str] = Column("VARCHAR")
    social_links: Optional[List[SocialLink]] = Column("ARRAY(ROW(?))")
    stats: Optional[ParentAccountStats] = Column("ROW(?)")
    supported_expense_types: Optional[List[str]] = Column("ARRAY(VARCHAR)")
    tags: Optional[List[str]] = Column("ARRAY(VARCHAR)")
    transaction_reports: Optional[TransactionReports] = Column("ROW(?)")
    transferwise: Optional[str] = Column("VARCHAR")
    twitter_handle: Optional[str] = Column("VARCHAR")
    type: Optional[str] = Column("VARCHAR")
    updated_at: Optional[str] = Column("VARCHAR")
    website: Optional[str] = Column("VARCHAR")


class TransferwiseAvailableCurrency(BaseModel):
    code: Optional[str] = Column("VARCHAR")
    min_invoice_amount: Optional[int] = Column("INTEGER")


class TransferwiseBalance(BaseModel):
    currency: Optional[str] = Column("VARCHAR")
    value: Optional[float] = Column("DOUBLE")
    value_in_cents: Optional[int] = Column("BIGINT")


class Transferwise(BaseModel):
    amount_batched: Optional[float] = Column("DOUBLE")
    available_currencies: Optional[List[TransferwiseAvailableCurrency]] = Column(
        "ARRAY(ROW(?))"
    )
    balances: Optional[List[TransferwiseBalance]] = Column("ARRAY(ROW(?))")
    id: Optional[str] = Column("VARCHAR")


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
    settings: Settings | None = Column("ROW(?)")
    supported_expense_types: List[str] | None = Column("ARRAY(VARCHAR)")
    categories: List[str] | None = Column("ARRAY(VARCHAR)")
    stats: Stats | None = Column("ROW(?)")
    can_have_changelog_updates: bool | None = Column("BOOLEAN")
    features: Features | None = Column("ROW(?)")
    policies: Policies | None = Column("ROW(?)")
    permissions: Permissions | None = Column("ROW(?)")
    transaction_reports: TransactionReports | None = Column("ROW(?)")
    description: str | None = Column("VARCHAR")
    website: str | None = Column("VARCHAR")
    background_image_url: str | None = Column("VARCHAR")
    tags: List[str] | None = Column("ARRAY(VARCHAR)")
    github_handle: str | None = Column("VARCHAR")
    repository_url: str | None = Column("VARCHAR")
    location: Location | None = Column("ROW(?)")
    parent_account: ParentAccount | None = Column("ROW(?)")
    twitter_handle: str | None = Column("VARCHAR")
    transferwise: Transferwise | None = Column("ROW(?)")
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
