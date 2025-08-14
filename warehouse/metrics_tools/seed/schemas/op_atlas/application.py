from datetime import datetime, timedelta

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Application(BaseModel):
    id: str = Column("VARCHAR")
    status: str = Column("VARCHAR")
    attestation_id: str = Column("VARCHAR")
    created_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    updated_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    round_id: str = Column("VARCHAR")
    project_id: str = Column("VARCHAR")
    category_id: str | None = Column("VARCHAR")
    dlt_load_id: str = Column("VARCHAR", column_name="_dlt_load_id")
    dlt_id: str = Column("VARCHAR", column_name="_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="op_atlas",
    table="application",
    base=Application,
    rows=[
        Application(
            id="9b30e87b-ab99-4597-a8df-e680253d3040",
            status="submitted",
            attestation_id="0xb2a3005794d9686eac0303cb6b7390f8a9512ab75e0bdd7615031907ba5751f4",
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=2),
            round_id="7",
            project_id="0xcc8d03e014e121d10602eeff729b755d5dc6a317df0d6302c8a9d3b5424aaba8",
            category_id=None,
            dlt_load_id="1739280186.8371842",
            dlt_id="emwqb4s/ZEKINQ",
        ),
        Application(
            id="c2bb3ee1-c756-457f-8962-8cb81dd338b8",
            status="submitted",
            attestation_id="0x8679e5fed1809cfa0648c5ea97f89141360f0f7014dab46b29fdeda220c4d6be",
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(days=1),
            round_id="7",
            project_id="0x08df6e20a3cfabbaf8f34d4f4d048fe7da40447c24be0f3ad513db6f13c755dd",
            category_id=None,
            dlt_load_id="1740658210.259455",
            dlt_id="ZpQhsIUeyGxSNg",
        ),
        Application(
            id="ed9641ae-c2d9-42a6-b4f4-db9a581a303a",
            status="submitted",
            attestation_id="0x36b284fa12802b777f4b2a1bc4a97671a0854147426228544d643a6e144aedfc",
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(days=1),
            round_id="8",
            project_id="0x08df6e20a3cfabbaf8f34d4f4d048fe7da40447c24be0f3ad513db6f13c755dd",
            category_id=None,
            dlt_load_id="1740658210.259455",
            dlt_id="Vymet4l5lAUQUQ",
        ),
        Application(
            id="e36460e5-584c-499f-b9b9-15a7b10467d9",
            status="submitted",
            attestation_id="0x067ddea7ac5c1a301589fb7e1c65921024d9dbc246b839d881b7d5ab57e469a7",
            created_at=datetime.now() - timedelta(days=2),
            updated_at=datetime.now() - timedelta(days=2),
            round_id="8",
            project_id="0xb98778ca9ff41446e2bc304f7b5d27f0fa7c2bcd11df19e22d1352c06698a1f6",
            category_id=None,
            dlt_load_id="1741694928.6535969",
            dlt_id="Ku6bM6XJx8gXAg",
        ),
    ],
)
