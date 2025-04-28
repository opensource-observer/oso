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
            to_project_name="1hive",
            amount=3026.0,
            funding_date=date(2023, 3, 29),
            from_funder_name="dao-drops-dorgtech",
            grant_pool_name="round_1",
            metadata="{\"application_name\": \"Gardens\", \"application_url\": \"https://daodrops.io/\", \"token_amount\": 3026, \"token_unit\": \"DAI\"}",
            file_path="data/funders/dao-drops-dorgtech/uploads/round_1.csv",
            dlt_load_id="1745609598.9714267",
            dlt_id="fDa+72E7QVpCiw",
        ),
        Funding(
            to_project_name="bankless-africa",
            amount=4690.0,
            funding_date=date(2023, 3, 29),
            from_funder_name="dao-drops-dorgtech",
            grant_pool_name="round_1",
            metadata="{\"application_name\": \"Bankless Africa\", \"application_url\": \"https://daodrops.io/\", \"token_amount\": 4690, \"token_unit\": \"DAI\"}",
            file_path="data/funders/dao-drops-dorgtech/uploads/round_1.csv",
            dlt_load_id="1745609598.9714267",
            dlt_id="2PFXowCkHSKVuA",
        ),
        Funding(
            to_project_name="crypto-stats",
            amount=1271.0,
            funding_date=date(2023, 3, 29),
            from_funder_name="dao-drops-dorgtech",
            grant_pool_name="round_1",
            metadata="{\"application_name\": \"CryptoStats\", \"application_url\": \"https://daodrops.io/\", \"token_amount\": 1271, \"token_unit\": \"DAI\"}",
            file_path="data/funders/dao-drops-dorgtech/uploads/round_1.csv",
            dlt_load_id="1745609598.9714267",
            dlt_id="FkqYxAaRjeS97A",
        ),
        Funding(
            to_project_name="eth-limo",
            amount=10530.0,
            funding_date=date(2023, 3, 29),
            from_funder_name="dao-drops-dorgtech",
            grant_pool_name="round_1",
            metadata="{\"application_name\": \"eth.limo\", \"application_url\": \"https://daodrops.io/\", \"token_amount\": 10530, \"token_unit\": \"DAI\"}",
            file_path="data/funders/dao-drops-dorgtech/uploads/round_1.csv",
            dlt_load_id="1745609598.9714267",
            dlt_id="UL+nWZMinz1Ivw",
        ),
        Funding(
            to_project_name="ethereum-attestation-service",
            amount=4539.0,
            funding_date=date(2023, 3, 29),
            from_funder_name="dao-drops-dorgtech",
            grant_pool_name="round_1",
            metadata="{\"application_name\": \"Ethereum Attestation Service (EAS)\", \"application_url\": \"https://daodrops.io/\", \"token_amount\": 4539, \"token_unit\": \"DAI\"}",
            file_path="data/funders/dao-drops-dorgtech/uploads/round_1.csv",
            dlt_load_id="1745609598.9714267",
            dlt_id="ylSjUk8lY6EUKQ",
        ),
    ],
)
