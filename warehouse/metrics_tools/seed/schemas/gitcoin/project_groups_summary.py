from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class ProjectGroupsSummary(BaseModel):
    latest_created_application: datetime | None = Column("TIMESTAMP")
    group_id: str | None = Column("STRING")
    latest_created_project_id: str | None = Column("STRING")
    total_amount_donated: float | None = Column("FLOAT")
    application_count: str | None = Column("STRING")
    latest_source: str | None = Column("STRING")
    title: str | None = Column("STRING")
    latest_payout_address: str | None = Column("STRING")
    latest_website: str | None = Column("STRING")
    latest_project_twitter: str | None = Column("STRING")
    latest_project_github: str | None = Column("STRING")

seed = SeedConfig(
    catalog="bigquery",
    schema="gitcoin",
    table="project_groups_summary",
    base=ProjectGroupsSummary,
    rows=[
        ProjectGroupsSummary(
            latest_created_application=None,
            group_id="9",
            latest_created_project_id="24",
            total_amount_donated=149366.99218694086,
            application_count="1",
            latest_source="cGrants",
            title="prysm by prysmatic labs",
            latest_payout_address="0x9b984d5a03980d8dc0a24506c968465424c81dbe",
            latest_website="https://prysmaticlabs.com",
            latest_project_twitter="prylabs",
            latest_project_github="prysmaticlabs",
        ),
        ProjectGroupsSummary(
            latest_created_application=None,
            group_id="17",
            latest_created_project_id="32",
            total_amount_donated=3602.6561301643951,
            application_count="1",
            latest_source="cGrants",
            title="vipnode",
            latest_payout_address="0x961aa96febee5465149a0787b03bfa14d8e9033f",
            latest_website="https://vipnode.org",
            latest_project_twitter="shazow",
            latest_project_github="vipnode",
        ),
        ProjectGroupsSummary(
            latest_created_application=None,
            group_id="40",
            latest_created_project_id="65",
            total_amount_donated=13903.780819571641,
            application_count="1",
            latest_source="cGrants",
            title="urllib3 python http library",
            latest_payout_address="0xdba411d32793e057cb69658cf0d16b55dffb652a",
            latest_website="https://urllib3.dev",
            latest_project_twitter="urllib3",
            latest_project_github="urllib3",
        ),
        ProjectGroupsSummary(
            latest_created_application=None,
            group_id="105",
            latest_created_project_id="139",
            total_amount_donated=19340.781846257298,
            application_count="1",
            latest_source="cGrants",
            title="defiprimecom",
            latest_payout_address="0xebdb626c95a25f4e304336b1adcad0521a1bdca1",
            latest_website="https://defiprime.com",
            latest_project_twitter="defiprime",
            latest_project_github="defiprime",
        ),
        ProjectGroupsSummary(
            latest_created_application=None,
            group_id="97",
            latest_created_project_id="152",
            total_amount_donated=8564.672186764423,
            application_count="1",
            latest_source="cGrants",
            title="shir ya khat podcast advanced ethereum for farsi speaking population",
            latest_payout_address="0x32cefb2dc869bbfe636f7547cda43f561bf88d5a",
            latest_website="https://shiryakhat.net",
            latest_project_twitter="shiryakhat",
            latest_project_github="shiryakhat",
        ),
        ProjectGroupsSummary(
            latest_created_application=None,
            group_id="117",
            latest_created_project_id="153",
            total_amount_donated=25318.088047606143,
            application_count="1",
            latest_source="cGrants",
            title="mailchain emaillike messaging built on blockchain protocols and decentralized storage",
            latest_payout_address="0x910119d96fcc68fc898a02b07b3a6316992af800",
            latest_website="https://github.com/mailchain/mailchain",
            latest_project_twitter="mailchain_xyz",
            latest_project_github="mailchain",
        ),
        ProjectGroupsSummary(
            latest_created_application=None,
            group_id="123",
            latest_created_project_id="159",
            total_amount_donated=17739.656864430835,
            application_count="1",
            latest_source="cGrants",
            title="mask network the portal to the new open internet legacy",
            latest_payout_address="0x934b510d4c9103e6a87aef13b816fb080286d649",
            latest_website="https://mask.io",
            latest_project_twitter="realmasknetwork",
            latest_project_github="dimensiondev",
        ),
        ProjectGroupsSummary(
            latest_created_application=None,
            group_id="143",
            latest_created_project_id="185",
            total_amount_donated=546.5775057601851,
            application_count="1",
            latest_source="cGrants",
            title="daism",
            latest_payout_address="0xfc2c722b8fe7b3ca277d349cbad6d2c5ce2ecf9c",
            latest_website="https://www.daism.io",
            latest_project_twitter="daism2019",
            latest_project_github="orgs",
        ),
        ProjectGroupsSummary(
            latest_created_application=None,
            group_id="151",
            latest_created_project_id="194",
            total_amount_donated=25935.630320599663,
            application_count="1",
            latest_source="cGrants",
            title="reach blockchain development platform",
            latest_payout_address="0x0639092a9c3d9467dd6f89a13213541c8a1e58b2",
            latest_website="http://reach.sh",
            latest_project_twitter="reachlang",
            latest_project_github="reach-sh",
        ),
        ProjectGroupsSummary(
            latest_created_application=None,
            group_id="154",
            latest_created_project_id="200",
            total_amount_donated=44702.476968072086,
            application_count="1",
            latest_source="cGrants",
            title="vyper smart contract language",
            latest_payout_address="0x70ccbe10f980d80b7ebaab7d2e3a73e87d67b775",
            latest_website="https://vyperlang.org",
            latest_project_twitter="vyperlang",
            latest_project_github="vyperlang",
        ),
    ],
)
