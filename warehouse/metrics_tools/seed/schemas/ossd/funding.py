from datetime import date

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Funding(BaseModel):
    """Stores funding information for open source projects"""

    to_project_name: str | None = Column(
        "VARCHAR", description="The name of the project receiving funding"
    )
    amount: float | None = Column("DOUBLE", description="The amount of funding")
    funding_date: date | None = Column(
        "DATE", description="The date the funding was provided"
    )
    from_funder_name: str | None = Column(
        "VARCHAR", description="The name of the organization providing funding"
    )
    grant_pool_name: str | None = Column(
        "VARCHAR", description="The name of the grant pool"
    )
    metadata: str | None = Column(
        "VARCHAR", description="Additional metadata about the grant in JSON format"
    )
    file_path: str | None = Column(
        "VARCHAR", description="The path to the file from which the data was loaded"
    )
    dlt_load_id: str = Column(
        "VARCHAR",
        column_name="_dlt_load_id",
        description="Internal ID used by the DLT system",
    )
    dlt_id: str = Column(
        "VARCHAR",
        column_name="_dlt_id",
        description="Another internal ID used by the DLT system",
    )


seed = SeedConfig(
    catalog="bigquery",
    schema="ossd",
    table="funding",
    base=Funding,
    rows=[
        Funding(
            to_project_name="onion-dao",
            amount=20799.2,
            funding_date=date(2023, 10, 19),
            from_funder_name="octant-golemfoundation",
            grant_pool_name="epoch_1",
            metadata='{"application_name": "OnionDAO", "application_url": "https://octant.app/project/1/0x20a1B17087482de88Fac6D7B5aE23A7175fd1395", "token_amount": 10.3996, "token_unit": "ETH"}',
            file_path="data/funders/octant-golemfoundation/uploads/epoch_1.csv",
            dlt_load_id="1745394617.0419211",
            dlt_id="n6q/LqrxBusp6Q",
        ),
        Funding(
            to_project_name="banklessdao",
            amount=8.4,
            funding_date=date(2023, 10, 19),
            from_funder_name="octant-golemfoundation",
            grant_pool_name="epoch_1",
            metadata='{"application_name": "Bankless DAO", "application_url": "https://octant.app/project/1/0xCf3efCE169acEC1B281C05E863F78acCF62BD944", "token_amount": 0.0042, "token_unit": "ETH"}',
            file_path="data/funders/octant-golemfoundation/uploads/epoch_1.csv",
            dlt_load_id="1745394617.0419211",
            dlt_id="CTgYN3P+MggfjA",
        ),
        Funding(
            to_project_name="dao-drops-dorgtech",
            amount=14886.0,
            funding_date=date(2023, 10, 19),
            from_funder_name="octant-golemfoundation",
            grant_pool_name="epoch_1",
            metadata='{"application_name": "DAO Drops", "application_url": "https://octant.app/project/1/0x1c01595f9534E33d411035AE99a4317faeC4f6Fe", "token_amount": 7.443, "token_unit": "ETH"}',
            file_path="data/funders/octant-golemfoundation/uploads/epoch_1.csv",
            dlt_load_id="1745394617.0419211",
            dlt_id="heka12VXw1HrYw",
        ),
        Funding(
            to_project_name="clrfund",
            amount=12923.6,
            funding_date=date(2023, 10, 19),
            from_funder_name="octant-golemfoundation",
            grant_pool_name="epoch_1",
            metadata='{"application_name": "Clr.fund", "application_url": "https://octant.app/project/1/0xAb6D6a37c5110d1377832c451C33e4fA16A9BA05", "token_amount": 6.4618, "token_unit": "ETH"}',
            file_path="data/funders/octant-golemfoundation/uploads/epoch_1.csv",
            dlt_load_id="1745394617.0419211",
            dlt_id="snKS6Oioy9bCbA",
        ),
        Funding(
            to_project_name="hypercerts",
            amount=55440.0,
            funding_date=date(2023, 10, 19),
            from_funder_name="octant-golemfoundation",
            grant_pool_name="epoch_1",
            metadata='{"application_name": "Hypercerts", "application_url": "https://octant.app/project/1/0x2DCDF80f439843D7E0aD1fEF9E7a439B7917eAc9", "token_amount": 27.72, "token_unit": "ETH"}',
            file_path="data/funders/octant-golemfoundation/uploads/epoch_1.csv",
            dlt_load_id="1745394617.0419211",
            dlt_id="IF+35Y9UqOAROw",
        ),
    ],
)
