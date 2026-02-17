import json

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class RpgfApplications(BaseModel):
    application_id: str | None = Column(
        "VARCHAR", description="Application ID from REST API"
    )
    source: str | None = Column(
        "VARCHAR",
        description="Source repo info (forge, url, repoName, ownerName) as JSON string",
    )
    account: str | None = Column(
        "VARCHAR", description="Account with accountId and driver as JSON string"
    )
    chain_data: str | None = Column(
        "VARCHAR",
        description="Chain data array with support items and totalEarned as JSON string",
    )
    dlt_load_id: str = Column("VARCHAR", column_name="_dlt_load_id")
    dlt_id: str = Column("VARCHAR", column_name="_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="drips",
    table="rpgf_applications",
    base=RpgfApplications,
    rows=[
        RpgfApplications(
            application_id="22faefcd-a56d-4560-9573-e6703d441b78",
            source=json.dumps(
                {
                    "forge": "GitHub",
                    "url": "https://github.com/CELtd/mechafil-jax",
                    "repoName": "mechafil-jax",
                    "ownerName": "CELtd",
                }
            ),
            account=json.dumps(
                {
                    "driver": "REPO",
                    "accountId": "80907513561425742910571596737190374466994210134331304819071675006976",
                }
            ),
            chain_data=json.dumps(
                [
                    {
                        "__typename": "ClaimedProjectData",
                        "chain": "FILECOIN",
                        "support": [
                            {
                                "__typename": "ProjectSupport",
                                "date": 1734364320000,
                                "weight": 500000,
                                "totalSplit": [
                                    {
                                        "amount": "60856500000000011",
                                        "tokenAddress": "0x60e1773636cf5e4a227d9ac24f20feca034ee25a",
                                    }
                                ],
                            }
                        ],
                        "totalEarned": [
                            {
                                "tokenAddress": "0x60e1773636cf5e4a227d9ac24f20feca034ee25a",
                                "amount": "1581298891827481111125",
                            }
                        ],
                    }
                ]
            ),
            dlt_load_id="1771257320.845481",
            dlt_id="rQErFOqQkKU7cQ",
        ),
        RpgfApplications(
            application_id="33bbaacc-b67d-5671-a684-f7814e552c89",
            source=json.dumps(
                {
                    "forge": "GitHub",
                    "url": "https://github.com/KenCloud-Tech/kenlabs-education",
                    "repoName": "kenlabs-education",
                    "ownerName": "KenCloud-Tech",
                }
            ),
            account=json.dumps(
                {
                    "driver": "REPO",
                    "accountId": "81058240255436682077438409847851217564154460141535144779148701660614",
                }
            ),
            chain_data=json.dumps(
                [
                    {
                        "__typename": "ClaimedProjectData",
                        "chain": "FILECOIN",
                        "support": [
                            {
                                "__typename": "DripListSupport",
                                "date": 1737040800000,
                                "weight": 166666,
                                "totalSplit": [
                                    {
                                        "amount": "116666200000000000",
                                        "tokenAddress": "0x60e1773636cf5e4a227d9ac24f20feca034ee25a",
                                    }
                                ],
                            }
                        ],
                        "totalEarned": [
                            {
                                "tokenAddress": "0x60e1773636cf5e4a227d9ac24f20feca034ee25a",
                                "amount": "1864986995718962500000",
                            }
                        ],
                    }
                ]
            ),
            dlt_load_id="1771257320.845481",
            dlt_id="bXYzABcDeFgHiJ",
        ),
        RpgfApplications(
            application_id="44ccddeef-c78e-6782-b795-g8925f663d90",
            source=None,
            account=json.dumps(
                {
                    "driver": "REPO",
                    "accountId": "80908805740114324836386940374142670747048935803478337467592873082880",
                }
            ),
            chain_data=None,
            dlt_load_id="1771257320.845481",
            dlt_id="cPQrSTuVwXyZaB",
        ),
    ],
)
