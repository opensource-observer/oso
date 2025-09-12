from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class L2beatProjects(BaseModel):
    """Stores L2beat project information for various blockchain projects"""

    id: str | None = Column("VARCHAR", description="Project identifier")
    name: str | None = Column("VARCHAR", description="Project name")
    slug: str | None = Column("VARCHAR", description="Project slug")
    type: str | None = Column(
        "VARCHAR", description="Project type (layer2, layer3, etc.)"
    )
    host_chain: str | None = Column("VARCHAR", description="Host blockchain")
    category: str | None = Column("VARCHAR", description="Project category")
    providers: str | None = Column("JSON", description="Technology providers")
    purposes: str | None = Column("JSON", description="Project purposes")
    is_archived: bool | None = Column(
        "BOOLEAN", description="Whether project is archived"
    )
    is_upcoming: bool | None = Column(
        "BOOLEAN", description="Whether project is upcoming"
    )
    is_under_review: bool | None = Column(
        "BOOLEAN", description="Whether project is under review"
    )
    badges: str | None = Column("JSON", description="Project badges")
    stage: str | None = Column("VARCHAR", description="Project stage")
    risks: str | None = Column("JSON", description="Project risks")
    tvs: str | None = Column("JSON", description="Total Value Secured data")
    short_name: str | None = Column("VARCHAR", description="Short project name")


seed = SeedConfig(
    catalog="bigquery",
    schema="l2beat",
    table="projects",
    base=L2beatProjects,
    rows=[
        L2beatProjects(
            id="prom",
            name="Prom",
            slug="prom",
            type="layer2",
            host_chain="Ethereum",
            category=None,
            providers='["Agglayer CDK"]',
            purposes='["Gaming","NFT"]',
            is_archived=False,
            is_upcoming=False,
            is_under_review=True,
            badges="[]",
            stage="Under review",
            risks='[{"description":"This risk is currently under review.","name":"Sequencer Failure","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"State Validation","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"Data Availability","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"Exit Window","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"Proposer Failure","sentiment":"UnderReview","value":"Under Review"}]',
            tvs='{"associatedTokens":[{"icon":"https://coin-images.coingecko.com/coins/images/8825/large/Ticker.png?1696508978","symbol":"PROM"}],"breakdown":{"associated":2138916.8,"btc":0,"canonical":2138918.8,"ether":0,"external":0,"native":0,"other":2138916.8,"stablecoin":1.98,"total":2138918.8},"change7d":0.0022129176514247284}',
            short_name=None,
        ),
        L2beatProjects(
            id="moonchain",
            name="MXCzkEVM Moonchain",
            slug="moonchain",
            type="layer3",
            host_chain="Arbitrum One",
            category=None,
            providers='["Taiko"]',
            purposes='["Universal"]',
            is_archived=False,
            is_upcoming=False,
            is_under_review=True,
            badges="[]",
            stage="Under review",
            risks='[{"description":"This risk is currently under review.","name":"Sequencer Failure","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"State Validation","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"Data Availability","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"Exit Window","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"Proposer Failure","sentiment":"UnderReview","value":"Under Review"}]',
            tvs='{"associatedTokens":[{"icon":"https://assets.coingecko.com/coins/images/4604/large/M_1-modified.png?1712206949","symbol":"MXC"}],"breakdown":{"associated":2057671.9,"btc":0,"canonical":2057703.9,"ether":30.41,"external":0,"native":0,"other":2057671.9,"stablecoin":1.62,"total":2057703.9},"change7d":-0.3691948996145956}',
            short_name="Moonchain",
        ),
        L2beatProjects(
            id="onyx",
            name="Onyx",
            slug="onyx",
            type="layer3",
            host_chain="Base Chain",
            category=None,
            providers='["Arbitrum"]',
            purposes='["Universal"]',
            is_archived=False,
            is_upcoming=False,
            is_under_review=True,
            badges='[{"action":{"id":"vm","type":"scalingFilter","value":"EVM"},"description":"This project uses the Ethereum Virtual Machine to run its smart contracts and supports the Solidity programming language","id":"EVM","name":"EVM","type":"VM"},{"action":{"type":"selfDaHighlight"},"description":"There is a Data Availability Committee that provides/attests to data availability","id":"DAC","name":"Data Availability Committee","type":"DA"},{"action":{"id":"stack","type":"scalingFilter","value":"Arbitrum"},"description":"The project is built on Arbitrum Orbit","id":"Orbit","name":"Built on Arbitrum Orbit","type":"Stack"},{"action":{"id":"raas","type":"scalingFilter","value":"Conduit"},"description":"This project was deployed via the rollup-as-a-service provider Conduit","id":"Conduit","name":"Conduit","type":"RaaS"}]',
            stage="Under review",
            risks='[{"description":"This risk is currently under review.","name":"Sequencer Failure","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"State Validation","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"Data Availability","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"Exit Window","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"Proposer Failure","sentiment":"UnderReview","value":"Under Review"}]',
            tvs='{"associatedTokens":[{"icon":"https://coin-images.coingecko.com/coins/images/24210/large/onyxlogo.jpg?1696523397","symbol":"XCN"}],"breakdown":{"associated":225871.81,"btc":0,"canonical":225871.81,"ether":0,"external":0,"native":0,"other":225871.81,"stablecoin":0,"total":225871.81},"change7d":-0.07999585192935588}',
            short_name=None,
        ),
        L2beatProjects(
            id="soonbase",
            name="soonBase",
            slug="soonbase",
            type="layer2",
            host_chain="Ethereum",
            category=None,
            providers=None,
            purposes='["Universal"]',
            is_archived=False,
            is_upcoming=False,
            is_under_review=True,
            badges="[]",
            stage="Under review",
            risks='[{"description":"This risk is currently under review.","name":"Sequencer Failure","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"State Validation","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"Data Availability","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"Exit Window","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"Proposer Failure","sentiment":"UnderReview","value":"Under Review"}]',
            tvs='{"associatedTokens":[],"breakdown":{"associated":0,"btc":0,"canonical":199959.33,"ether":199123.11,"external":0,"native":0,"other":0,"stablecoin":836.22,"total":199959.33},"change7d":-0.05407071218836523}',
            short_name=None,
        ),
        L2beatProjects(
            id="powerloom",
            name="Powerloom",
            slug="powerloom",
            type="layer2",
            host_chain="Ethereum",
            category=None,
            providers='["Arbitrum"]',
            purposes='["Universal"]',
            is_archived=False,
            is_upcoming=False,
            is_under_review=True,
            badges="[]",
            stage="Under review",
            risks='[{"description":"This risk is currently under review.","name":"Sequencer Failure","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"State Validation","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"Data Availability","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"Exit Window","sentiment":"UnderReview","value":"Under Review"},{"description":"This risk is currently under review.","name":"Proposer Failure","sentiment":"UnderReview","value":"Under Review"}]',
            tvs='{"associatedTokens":[{"icon":"https://coin-images.coingecko.com/coins/images/53319/large/powerloom-200px.png?1736086027","symbol":"POWER"}],"breakdown":{"associated":185373.69,"btc":0,"canonical":185373.69,"ether":0,"external":0,"native":0,"other":185373.69,"stablecoin":0,"total":185373.69},"change7d":-0.06293212845899909}',
            short_name=None,
        ),
    ],
)
