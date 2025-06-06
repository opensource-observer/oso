from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class PublishedContract(BaseModel):
    id: str = Column("VARCHAR")
    contract: str = Column("VARCHAR")
    chain_id: int = Column("BIGINT")
    deployer: str = Column("VARCHAR")
    deployment_tx: str = Column("VARCHAR")
    signature: str = Column("VARCHAR")
    verification_chain_id: int = Column("BIGINT")
    project_id: str = Column("VARCHAR")
    created_at: datetime = Column("TIMESTAMP(6) WITH TIME ZONE")
    revoked_at: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    dlt_load_id: str = Column("VARCHAR", column_name="_dlt_load_id")
    dlt_id: str = Column("VARCHAR", column_name="_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="op_atlas",
    table="published_contract",
    base=PublishedContract,
    rows=[
        PublishedContract(
            id="0x4507d81c22a94b5641876a48a858dda5db4d63005eaf4e304260b6ace69321dd",
            contract="0x03D6ec933E452283a0CaC468F487F327d1baE9ba",
            chain_id=480,
            deployer="0xBDF4dAb6e1eb99cFc1472d953A6394495cE22A2D",
            deployment_tx="0xa7ffb3364efe4f1948cc1fa64205b2a61ca5bef9db599bb6b6801597631ab344",
            signature="0xf333f11b19c82f806fd8b2504f0e4b5edd4e07bd00ea5700a42df6403fb5c4346b0e5bfe73bba790e9d198678d76088c6c7525b5f04d592145d64dd2df44391c1c",
            verification_chain_id=480,
            project_id="0x041baee0d8c07a4e89e4c6c19410d8f6cd0a8439cbe8ea0687bf9a504f1c6a88",
            created_at=datetime.fromisoformat("2025-06-05 15:23:25.549000+00:00"),
            revoked_at=None,
            dlt_load_id="1749173200.2323897",
            dlt_id="qWNs1Dwxr99aZg",
        ),
        PublishedContract(
            id="0xd930c08c49d9a677d2556ec29c6e14691101f11b113ceca681bcc69a481e5beb",
            contract="0x4c589069E01118663827f364C7435cEBACbbdb4F",
            chain_id=480,
            deployer="0x5868181f646464621eF396f211bbb18Eee2bF5DD",
            deployment_tx="0x5ea854d2ddafd39c9136bdd969d2fdc01c7387353c5c828fc50f279a806ec3d2",
            signature="0x3674cafee062f4bfc87dc090d005932aeeefc08325d3ff8448fc05feaa8ec95525c47663afa5f0b6874bd98e7c6e69805952c85d30217d489fbc4eb43a2bd2a41b",
            verification_chain_id=480,
            project_id="0xe2ef3fbfd10df401a0221939359e96af29805db8936c1199ae7532262c69ec5f",
            created_at=datetime.fromisoformat("2025-06-05 14:02:26.602000+00:00"),
            revoked_at=None,
            dlt_load_id="1749173200.2323897",
            dlt_id="fya7ddYFBbUhPQ",
        ),
        PublishedContract(
            id="0x5673ca15d7fdbc9bef8eaf8a581983e0cc1fd2d854e6054812897218f70f8c72",
            contract="0x22615616FD236639c252ed572CF668B018198B12",
            chain_id=480,
            deployer="0x5868181f646464621eF396f211bbb18Eee2bF5DD",
            deployment_tx="0xa11af1eeb0f2a620e527ac45b40cca681b4347749a92a09ae7dc804f42f1543d",
            signature="0x3674cafee062f4bfc87dc090d005932aeeefc08325d3ff8448fc05feaa8ec95525c47663afa5f0b6874bd98e7c6e69805952c85d30217d489fbc4eb43a2bd2a41b",
            verification_chain_id=480,
            project_id="0xe2ef3fbfd10df401a0221939359e96af29805db8936c1199ae7532262c69ec5f",
            created_at=datetime.fromisoformat("2025-06-05 14:02:26.602000+00:00"),
            revoked_at=None,
            dlt_load_id="1749173200.2323897",
            dlt_id="fX2/7YAtnCe+Cw",
        ),
        PublishedContract(
            id="0x32f43d0e52492fb8a00d746c54258a7691a0157ba01cc8c5f1469444f507200f",
            contract="0xD4c6db823D0Eb093115b177d239f4967155bAA75",
            chain_id=480,
            deployer="0x5868181f646464621eF396f211bbb18Eee2bF5DD",
            deployment_tx="",
            signature="0x3674cafee062f4bfc87dc090d005932aeeefc08325d3ff8448fc05feaa8ec95525c47663afa5f0b6874bd98e7c6e69805952c85d30217d489fbc4eb43a2bd2a41b",
            verification_chain_id=10,
            project_id="0xe2ef3fbfd10df401a0221939359e96af29805db8936c1199ae7532262c69ec5f",
            created_at=datetime.fromisoformat("2025-06-05 14:02:26.602000+00:00"),
            revoked_at=datetime.fromisoformat("2025-06-05 14:06:24.574000+00:00"),
            dlt_load_id="1749173200.2323897",
            dlt_id="2tRdo9UVNArDuw",
        ),
        PublishedContract(
            id="0x6907e93afd002394cd5e08fc119f3b9c7a345a22eb095d8354febcb493d23baa",
            contract="0x8d623f08f3C1b4dB904e985EBD6E3feAa9256674",
            chain_id=480,
            deployer="0x5868181f646464621eF396f211bbb18Eee2bF5DD",
            deployment_tx="",
            signature="0x3674cafee062f4bfc87dc090d005932aeeefc08325d3ff8448fc05feaa8ec95525c47663afa5f0b6874bd98e7c6e69805952c85d30217d489fbc4eb43a2bd2a41b",
            verification_chain_id=10,
            project_id="0xe2ef3fbfd10df401a0221939359e96af29805db8936c1199ae7532262c69ec5f",
            created_at=datetime.fromisoformat("2025-06-05 14:02:26.602000+00:00"),
            revoked_at=datetime.fromisoformat("2025-06-05 14:06:24.574000+00:00"),
            dlt_load_id="1749173200.2323897",
            dlt_id="Z/hUF85gUpssSw",
        ),
    ],
)
