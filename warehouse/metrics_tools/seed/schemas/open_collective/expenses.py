from datetime import datetime, timedelta
from typing import Any, Dict

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Expenses(BaseModel):
    id: str | None = Column("VARCHAR")
    legacy_id: int | None = Column("BIGINT")
    group: str | None = Column("VARCHAR", "group")
    type: str | None = Column("VARCHAR")
    kind: str | None = Column("VARCHAR")
    description: str | None = Column("VARCHAR")
    amount: Dict[str, Any] | None = Column("JSON")
    amount_in_host_currency: Dict[str, Any] | None = Column("JSON")
    host_currency_fx_rate: float | None = Column("DOUBLE")
    net_amount: Dict[str, Any] | None = Column("JSON")
    net_amount_in_host_currency: Dict[str, Any] | None = Column("JSON")
    tax_amount: Dict[str, Any] | None = Column("JSON")
    tax_info: Dict[str, Any] | None = Column("JSON")
    platform_fee: Dict[str, Any] | None = Column("JSON")
    host_fee: Dict[str, Any] | None = Column("JSON")
    payment_processor_fee: Dict[str, Any] | None = Column("JSON")
    account: Dict[str, Any] | None = Column("JSON")
    from_account: Dict[str, Any] | None = Column("JSON")
    to_account: Dict[str, Any] | None = Column("JSON")
    expense: Dict[str, Any] | None = Column("JSON")
    order: Dict[str, Any] | None = Column("JSON", "order")
    created_at: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    updated_at: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    is_refunded: bool | None = Column("BOOLEAN")
    is_refund: bool | None = Column("BOOLEAN")
    is_disputed: bool | None = Column("BOOLEAN")
    is_in_review: bool | None = Column("BOOLEAN")
    payment_method: Dict[str, Any] | None = Column("JSON")
    payout_method: Dict[str, Any] | None = Column("JSON")
    is_order_rejected: bool | None = Column("BOOLEAN")
    merchant_id: str | None = Column("VARCHAR")
    invoice_template: str | None = Column("VARCHAR")
    host: Dict[str, Any] | None = Column("JSON")
    dlt_load_id: str = Column("VARCHAR", "_dlt_load_id")
    dlt_id: str = Column("VARCHAR", "_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="open_collective",
    table="expenses",
    base=Expenses,
    rows=[
        Expenses(
            id="1",
            legacy_id=1,
            group="group1",
            type="type1",
            kind="kind1",
            description="description1",
            amount={},
            amount_in_host_currency={},
            host_currency_fx_rate=1.0,
            net_amount={},
            net_amount_in_host_currency={},
            tax_amount={},
            tax_info={},
            platform_fee={},
            host_fee={},
            payment_processor_fee={},
            account={},
            from_account={},
            to_account={},
            expense={},
            order={},
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=2),
            is_refunded=False,
            is_refund=False,
            is_disputed=False,
            is_in_review=False,
            payment_method={},
            payout_method={},
            is_order_rejected=False,
            merchant_id="merchant1",
            invoice_template="template1",
            host={},
            dlt_load_id="load_id1",
            dlt_id="id1",
        ),
        Expenses(
            id="2",
            legacy_id=2,
            group="group2",
            type="type2",
            kind="kind2",
            description="description2",
            amount={},
            amount_in_host_currency={},
            host_currency_fx_rate=1.0,
            net_amount={},
            net_amount_in_host_currency={},
            tax_amount={},
            tax_info={},
            platform_fee={},
            host_fee={},
            payment_processor_fee={},
            account={},
            from_account={},
            to_account={},
            expense={},
            order={},
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(days=1),
            is_refunded=False,
            is_refund=False,
            is_disputed=False,
            is_in_review=False,
            payment_method={},
            payout_method={},
            is_order_rejected=False,
            merchant_id="merchant2",
            invoice_template="template2",
            host={},
            dlt_load_id="load_id2",
            dlt_id="id2",
        ),
    ],
)
