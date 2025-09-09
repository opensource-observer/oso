import json

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class FundingRound(BaseModel):
    """Funding round information"""

    name: str
    announced_date: str
    lead_investors: list[str]
    amount_raised: int
    amount_raised_currency: str
    num_investors: int


class CompanyData(BaseModel):
    """Stores company information from Core Signal API"""

    id: int = Column(
        "BIGINT", description="Company record identification key in the API"
    )
    source_id: str = Column(
        "VARCHAR", description="Identifier assigned by Professional Network"
    )
    company_name: str | None = Column("VARCHAR", description="Company name")
    company_name_alias: list[str] = Column(
        "JSON", description="All name variations associated with the company"
    )
    company_legal_name: str | None = Column("VARCHAR", description="Legal company name")
    website: str | None = Column("VARCHAR", description="Website URL")
    website_alias: list[str] = Column(
        "JSON",
        description="All possible company website variations (collected from our firmographic sources)",
    )
    twitter_url: list[str] = Column("JSON", description="Twitter profile URL")
    crunchbase_url: str | None = Column("VARCHAR", description="Crunchbase profile URL")
    github_url: list[str] = Column("JSON", description="GitHub profile URL")
    funding_rounds: str = Column("JSON", description="List of completed funding rounds")
    dlt_load_id: str | None = Column(
        "VARCHAR",
        column_name="_dlt_load_id",
        description="Internal only value used by DLT. This is the unix timestamp of the load job that scraped the data",
    )
    dlt_id: str | None = Column(
        "VARCHAR",
        column_name="_dlt_id",
        description="Internal only unique value for the row",
    )


seed = SeedConfig(
    catalog="bigquery_oso_dynamic",
    schema="oso",
    table="coresignal_company_data",
    base=CompanyData,
    rows=[
        CompanyData(
            id=1,
            source_id="1",
            company_name="Oso",
            company_name_alias=["Opensource Observer"],
            company_legal_name="Oso Inc.",
            website="https://opensource.observer",
            website_alias=[],
            twitter_url=["https://twitter.com/oso"],
            crunchbase_url="https://www.crunchbase.com/organization/oso",
            github_url=["https://github.com/oso"],
            dlt_load_id="dlt_load_1",
            dlt_id="dlt_id_1",
            funding_rounds=json.dumps(
                [
                    FundingRound(
                        name="Seed",
                        announced_date="2020-01-01",
                        lead_investors=["Investor A", "Investor B"],
                        amount_raised=5000000,
                        amount_raised_currency="USD",
                        num_investors=2,
                    ),
                    FundingRound(
                        name="Series A",
                        announced_date="2021-06-15",
                        lead_investors=["Investor C"],
                        amount_raised=15000000,
                        amount_raised_currency="USD",
                        num_investors=3,
                    ),
                ],
                default=lambda x: x.dict(),
            ),
        ),
        CompanyData(
            id=2,
            source_id="2",
            company_name="Google",
            company_name_alias=["Google"],
            company_legal_name="Google LLC",
            website="https://google.com",
            website_alias=["Google"],
            twitter_url=["https://twitter.com/google"],
            crunchbase_url="https://www.crunchbase.com/organization/google",
            github_url=["https://github.com/google"],
            dlt_load_id="dlt_load_1",
            dlt_id="dlt_id_2",
            funding_rounds=json.dumps(
                [
                    FundingRound(
                        name="Series A",
                        announced_date="1998-08-19",
                        lead_investors=["Investor X", "Investor Y"],
                        amount_raised=250000,
                        amount_raised_currency="USD",
                        num_investors=2,
                    ),
                    FundingRound(
                        name="Series B",
                        announced_date="1999-04-01",
                        lead_investors=["Investor Z"],
                        amount_raised=2500000,
                        amount_raised_currency="USD",
                        num_investors=3,
                    ),
                ],
                default=lambda x: x.dict(),
            ),
        ),
    ],
)
