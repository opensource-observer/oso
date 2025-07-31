from typing import List

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class Taxonomy(BaseModel):
    """Stores crypto ecosystem taxonomy data from the crypto-ecosystems repository"""

    repo_url: str | None = Column("VARCHAR", description="The GitHub repository URL")
    branch: List[str] | None = Column(
        "ARRAY<VARCHAR>", description="List of ecosystem branches/categories"
    )
    tags: List[str] | None = Column(
        "ARRAY<VARCHAR>", description="List of tags associated with the repository"
    )
    eco_name: str | None = Column("VARCHAR", description="The ecosystem name")


seed = SeedConfig(
    catalog="bigquery",
    schema="crypto_ecosystems",
    table="taxonomy",
    base=Taxonomy,
    rows=[
        Taxonomy(
            repo_url="https://github.com/mcdexio/mai3-arb-bridge-graph",
            branch=[
                "Ethereum Virtual Machine Stack",
                "EVM Compatible L1 and L2",
                "EVM Compatible Layer 1s",
                "BNB Chain",
                "MCDEX",
            ],
            tags=[],
            eco_name="General",
        ),
        Taxonomy(
            repo_url="https://github.com/MELD-labs/cardano-serialization-lib",
            branch=[
                "Ethereum Virtual Machine Stack",
                "EVM Compatible L1 and L2",
                "EVM Compatible Layer 1s",
                "BNB Chain",
                "Meld",
            ],
            tags=[],
            eco_name="General",
        ),
        Taxonomy(
            repo_url="https://github.com/Mirror-Protocol/mirror-airdrop",
            branch=[
                "Ethereum Virtual Machine Stack",
                "EVM Compatible L1 and L2",
                "EVM Compatible Layer 1s",
                "BNB Chain",
                "Mirror Protocol",
            ],
            tags=[],
            eco_name="General",
        ),
        Taxonomy(
            repo_url="https://github.com/AnotherWorldDAO/ue5-treasurehunt",
            branch=[],
            tags=[],
            eco_name="Optimism",
        ),
        Taxonomy(
            repo_url="https://github.com/AngleProtocol/angle-governance",
            branch=["Angle Protocol"],
            tags=[],
            eco_name="Optimism",
        ),
        Taxonomy(
            repo_url="https://github.com/functionland/react-native-fula",
            branch=[
                "Ethereum Virtual Machine Stack",
                "EVM Compatible L1 and L2",
                "EVM Compatible Layer 1s",
                "Polygon",
                "Functionland",
            ],
            tags=["#mobile", "#protocol"],
            eco_name="General",
        ),
        Taxonomy(
            repo_url="https://github.com/tamago-labs/story-build",
            branch=["Story Protocol"],
            tags=["#community", "#application"],
            eco_name="Ethereum",
        ),
    ],
)
