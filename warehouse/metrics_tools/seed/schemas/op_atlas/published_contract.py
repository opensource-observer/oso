from datetime import datetime, timedelta

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
            created_at=datetime.now() - timedelta(days=2),
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
            created_at=datetime.now() - timedelta(days=1),
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
            created_at=datetime.now() - timedelta(days=1),
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
            created_at=datetime.now() - timedelta(days=1),
            revoked_at=datetime.now() - timedelta(days=1),
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
            created_at=datetime.now() - timedelta(days=1),
            revoked_at=datetime.now() - timedelta(days=1),
            dlt_load_id="1749173200.2323897",
            dlt_id="Z/hUF85gUpssSw",
        ),
        PublishedContract(
            id="0x7411613f87fd80d80fa99430b80a8a9ac0a6be4030ed2bd3b76715448102d2bd",
            contract="0x0000000071727De22E5E9d8BAf0edAc6f37da032",
            chain_id=8453,
            deployer="0x81ead4918134AE386dbd04346216E20AB8F822C4",
            deployment_tx="0xa3382f65bab116e6dfe68ef4d96415515bca45b86072725d45d00df2010ac5b0",
            signature="0x0",
            verification_chain_id=8453,
            project_id="0xb98778ca9ff41446e2bc304f7b5d27f0fa7c2bcd11df19e22d1352c06698a1f6",
            created_at=datetime.now() - timedelta(days=2),
            revoked_at=None,
            dlt_load_id="1749213070.9063745",
            dlt_id="Dzg/2SLNngxlVA",
        ),
        PublishedContract(
            id="0x5d82ba0e917522fba6f5f368189698fc8f2abc3c444b7d5bdacf214d895781a6",
            contract="0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789",
            chain_id=10,
            deployer="0x81ead4918134AE386dbd04346216E20AB8F822C4",
            deployment_tx="0xcddea14be9b486fd1c7311dbaf58fe13f1316eebd16d350bed3573b90e9515b8",
            signature="0x45a72fed635dc10fd4e12b025c3e0ba4f336c735f982d4d645509f06a01365425119d7245e6da3612e431e7f5272cfc2b103d0f8cbe9e52a970c2288e64bdd7b1c",
            verification_chain_id=10,
            project_id="0xb98778ca9ff41446e2bc304f7b5d27f0fa7c2bcd11df19e22d1352c06698a1f6",
            created_at=datetime.now() - timedelta(days=2),
            revoked_at=None,
            dlt_load_id="1749213070.9063745",
            dlt_id="GyQ68ZhjXmuyVw",
        ),
        PublishedContract(
            id="0x888728b4f8d7db79061274c83642f42abfb061d855b10576a88d50242f832529",
            contract="0x0000000071727De22E5E9d8BAf0edAc6f37da032",
            chain_id=10,
            deployer="0x81ead4918134AE386dbd04346216E20AB8F822C4",
            deployment_tx="0x1f5b834a37c7d91b9541a2b35f8d0bffcf27d4b0f2656f793478db8c8c029d6a",
            signature="0x0",
            verification_chain_id=10,
            project_id="0xb98778ca9ff41446e2bc304f7b5d27f0fa7c2bcd11df19e22d1352c06698a1f6",
            created_at=datetime.now() - timedelta(days=2),
            revoked_at=None,
            dlt_load_id="1749213070.9063745",
            dlt_id="f4WjlJzfpqYtHQ",
        ),
    ],
)
