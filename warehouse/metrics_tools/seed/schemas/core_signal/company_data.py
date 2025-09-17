import json
from datetime import datetime, timedelta

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
            twitter_url=["https://twitter.com/oso", "https://x.com/oso_labs"],
            crunchbase_url="https://www.crunchbase.com/organization/oso",
            github_url=[
                "https://github.com/oso",
                "https://github.com/oso-labs",
                "https://github.com/opensource-observer/oso",
            ],
            dlt_load_id="dlt_load_1",
            dlt_id="dlt_id_1",
            funding_rounds=json.dumps(
                [
                    FundingRound(
                        name="Seed",
                        announced_date=datetime.now().strftime("%Y-%m-%d"),
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
                    FundingRound(
                        name="Series B",
                        announced_date=(datetime.now() - timedelta(days=2)).strftime(
                            "%Y-%m-%d"
                        ),
                        lead_investors=["Investor D", "Investor E"],
                        amount_raised=25000000,
                        amount_raised_currency="USD",
                        num_investors=4,
                    ),
                    FundingRound(
                        name="Bridge Round",
                        announced_date=(datetime.now() - timedelta(days=4)).strftime(
                            "%Y-%m-%d"
                        ),
                        lead_investors=["Investor F"],
                        amount_raised=8000000,
                        amount_raised_currency="USD",
                        num_investors=2,
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
        CompanyData(
            id=3,
            source_id="3",
            company_name="Project 1 Inc",
            company_name_alias=["Project1", "Project One"],
            company_legal_name="Project 1 Inc.",
            website="https://project1.com",
            website_alias=["https://www.project1.com"],
            twitter_url=["https://twitter.com/project1"],
            crunchbase_url="https://www.crunchbase.com/organization/project1",
            github_url=["https://github.com/project1"],
            dlt_load_id="dlt_load_1",
            dlt_id="dlt_id_3",
            funding_rounds=json.dumps(
                [
                    FundingRound(
                        name="Seed",
                        announced_date="2023-01-15",
                        lead_investors=["Tech Investor A"],
                        amount_raised=2000000,
                        amount_raised_currency="USD",
                        num_investors=1,
                    ),
                    FundingRound(
                        name="Series A",
                        announced_date="2024-03-20",
                        lead_investors=["VC Fund B", "Angel Investor C"],
                        amount_raised=8000000,
                        amount_raised_currency="USD",
                        num_investors=3,
                    ),
                ],
                default=lambda x: x.dict(),
            ),
        ),
        CompanyData(
            id=4,
            source_id="4",
            company_name="Project 2 Corp",
            company_name_alias=["Project2", "Project Two"],
            company_legal_name="Project 2 Corporation",
            website="https://project2.com",
            website_alias=["https://www.project2.com"],
            twitter_url=["https://twitter.com/project2"],
            crunchbase_url="https://www.crunchbase.com/organization/project2",
            github_url=["https://github.com/project2"],
            dlt_load_id="dlt_load_1",
            dlt_id="dlt_id_4",
            funding_rounds=json.dumps(
                [
                    FundingRound(
                        name="Pre-Seed",
                        announced_date="2022-11-10",
                        lead_investors=["Early Stage Fund"],
                        amount_raised=500000,
                        amount_raised_currency="USD",
                        num_investors=1,
                    ),
                    FundingRound(
                        name="Seed",
                        announced_date="2023-08-05",
                        lead_investors=["Seed Fund X"],
                        amount_raised=3000000,
                        amount_raised_currency="USD",
                        num_investors=2,
                    ),
                ],
                default=lambda x: x.dict(),
            ),
        ),
        CompanyData(
            id=5,
            source_id="5",
            company_name="No Match Corp",
            company_name_alias=["NoMatch"],
            company_legal_name="No Match Corporation",
            website="https://nomatch.com",
            website_alias=["https://www.nomatch.com"],
            twitter_url=["https://twitter.com/nomatch"],
            crunchbase_url="https://www.crunchbase.com/organization/nomatch",
            github_url=["https://github.com/nomatch"],
            dlt_load_id="dlt_load_1",
            dlt_id="dlt_id_5",
            funding_rounds=json.dumps(
                [
                    FundingRound(
                        name="Seed",
                        announced_date="2023-05-15",
                        lead_investors=["Random Investor"],
                        amount_raised=1000000,
                        amount_raised_currency="USD",
                        num_investors=1,
                    ),
                ],
                default=lambda x: x.dict(),
            ),
        ),
    ],
)
