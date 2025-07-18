
from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class OptimismAttestations(BaseModel):
    """Ethereum Attestation Service attestations"""

    id: str = Column("TEXT", description="The id of the attestation")
    data: str = Column("TEXT", description="Raw attestation data")
    decoded_data_json: str = Column("TEXT", description="Decoded JSON data of the attestation")
    recipient: str = Column("VARCHAR", description="The recipient address of the attestation")
    attester: str = Column("VARCHAR", description="The attester address")
    time: int = Column("INTEGER", description="Timestamp of the attestation")
    time_created: int = Column("INTEGER", description="Timestamp when the attestation was created")
    expiration_time: int | None = Column("INTEGER", description="Expiration timestamp")
    revocation_time: int | None = Column("INTEGER", description="Revocation timestamp")
    ref_uid: str = Column("VARCHAR", description="Reference UID")
    schema_id: str = Column("VARCHAR", description="Schema ID")
    ipfs_hash: str = Column("TEXT", description="IPFS hash")
    is_offchain: bool = Column("BOOLEAN", description="Whether the attestation is offchain")


seed = SeedConfig(
    catalog="bigquery",
    schema="ethereum_attestation_service_optimism",
    table="attestations",
    base=OptimismAttestations,
    rows=[
        OptimismAttestations(
            id="0x0f006d6d25bd2b42522ff9d9907912b879efb433e7e245469192bff1235de177",
            data="0x0000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000013700000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001b416e74696361707475726520436f6d6d697373696f6e204c6561640000000000",
            decoded_data_json='[{"name":"govSeason","type":"string","signature":"string govSeason","value":{"name":"govSeason","type":"string","value":"7"}},{"name":"govRole","type":"string","signature":"string govRole","value":{"name":"govRole","type":"string","value":"Anticapture Commission Lead"}}]',
            recipient="0x94db037207f6fb697dbd33524aadffd108819dc8",
            attester="0xe4553b743e74da3424ac51f8c1e586fd43ae226f",
            time=1750783757,
            time_created=1750783759,
            expiration_time=0,
            revocation_time=0,
            ref_uid="0x0000000000000000000000000000000000000000000000000000000000000000",
            schema_id="0xef874554718a2afc254b064e5ce9c58c9082fb9f770250499bf406fc112bd315",
            ipfs_hash="",
            is_offchain=False,
        ),
        OptimismAttestations(
            id="0x9630ca1e352e4bf6b1e93dfc85142f803eef3af97df2865929066f7baa9c3aa1",
            data="0x0000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000013700000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001d416e74696361707475726520436f6d6d697373696f6e204d656d626572000000",
            decoded_data_json='[{"name":"govSeason","type":"string","signature":"string govSeason","value":{"name":"govSeason","type":"string","value":"7"}},{"name":"govRole","type":"string","signature":"string govRole","value":{"name":"govRole","type":"string","value":"Anticapture Commission Member"}}]',
            recipient="0xdcf7be2ff93e1a7671724598b1526f3a33b1ec25",
            attester="0xe4553b743e74da3424ac51f8c1e586fd43ae226f",
            time=1750783757,
            time_created=1750783762,
            expiration_time=0,
            revocation_time=0,
            ref_uid="0x0000000000000000000000000000000000000000000000000000000000000000",
            schema_id="0xef874554718a2afc254b064e5ce9c58c9082fb9f770250499bf406fc112bd315",
            ipfs_hash="",
            is_offchain=False,
        ),
        OptimismAttestations(
            id="0xbf450a306066dde73485dfb31ebb4d4cae0b111d2c1ebacc572d51e6b34efa04",
            data="0x0000000000000000000000000000000000000000000000000000000000000001",
            decoded_data_json='[{"name":"isTopDelegate","type":"bool","signature":"bool isTopDelegate","value":{"name":"isTopDelegate","type":"bool","value":true}}]',
            recipient="0x22e2f326fe5a1d07e1214eb1c08346fd816e8375",
            attester="0xfd620d657316f96186b3a9e3c8b97ed83281efdb",
            time=1750825591,
            time_created=1750825604,
            expiration_time=0,
            revocation_time=1750826369,
            ref_uid="0x0000000000000000000000000000000000000000000000000000000000000000",
            schema_id="0x8e2611b956fe603041d7fea2c8616c5e0dfb50becf30f640ab3154e4534eecd9",
            ipfs_hash="",
            is_offchain=False,
        ),
        OptimismAttestations(
            id="0x19408f4fbbfdcad14668cadbbe8a3ed7d3bcd770d94427e62d55310d7908e763",
            data='{"sig":{"domain":{"name":"EAS Attestation","version":"0.28","chainId":10,"verifyingContract":"0xd64059A36EdC1e278BDAB1256bB887668Fe33151"},"primaryType":"Attest","types":{"Attest":[{"name":"version","type":"uint16"},{"name":"schema","type":"bytes32"},{"name":"recipient","type":"address"},{"name":"time","type":"uint64"},{"name":"expirationTime","type":"uint64"},{"name":"revocable","type":"bool"},{"name":"refUID","type":"bytes32"},{"name":"data","type":"bytes"}]},"signature":{"r":"0xa033413bfc8638f17740789836029c859de327953900cd3e580e89f336f3595c","s":"0x0a7067260158d1d37c9264d2d312cd0c1c0fcb4b6940676d531d4d66bc09860a","v":28},"uid":"0x19408f4fbbfdcad14668cadbbe8a3ed7d3bcd770d94427e62d55310d7908e763","message":{"version":1,"schema":"0x818c5b73a39cc2c1bfeec619eb20f54bcf89624087c0e8943342da4fbbb38bc0","recipient":"0x000000187c72ee4a4120a3E626425595a34F185B","time":"1691693656","expirationTime":0,"revocable":true,"refUID":"0x0000000000000000000000000000000000000000000000000000000000000000","data":"0xef38251028ac2fe9e0e2ea4c4fd38abd4cb1ab591073cb038caf384352a3fd490000000000000000000000000000000000000000000000000000000000000080000000000000000000000000f01dd015bc442d872275a79b9cae84a6ff9b2a2700000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000000d63686f6d74616e612e746f776e00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e746f776e2d61776172656e657373000000000000000000000000000000000000"}},"signer":"0x888811A117405f323BabfB415c6D61F678e967dA"}',
            decoded_data_json='[{"name":"referrerNode","type":"bytes32","signature":"bytes32 referrerNode","value":{"name":"referrerNode","type":"bytes32","value":"0xef38251028ac2fe9e0e2ea4c4fd38abd4cb1ab591073cb038caf384352a3fd49"}},{"name":"referrerDomain","type":"string","signature":"string referrerDomain","value":{"name":"referrerDomain","type":"string","value":"chomtana.town"}},{"name":"referrerWallet","type":"address","signature":"address referrerWallet","value":{"name":"referrerWallet","type":"address","value":"0xf01Dd015Bc442d872275A79b9caE84A6ff9B2A27"}},{"name":"campaign","type":"string","signature":"string campaign","value":{"name":"campaign","type":"string","value":"town-awareness"}}]',
            recipient="0x000000187c72ee4a4120a3e626425595a34f185b",
            attester="0x888811a117405f323babfb415c6d61f678e967da",
            time=1691693656,
            time_created=1691693657,
            expiration_time=0,
            revocation_time=0,
            ref_uid="0x0000000000000000000000000000000000000000000000000000000000000000",
            schema_id="0x818c5b73a39cc2c1bfeec619eb20f54bcf89624087c0e8943342da4fbbb38bc0",
            ipfs_hash="QmYUC4RFukmLPE1qC2m6C1iv81ojJ9jLNSPHHsFpRvQi6F",
            is_offchain=True,
        ),
        OptimismAttestations(
            id="0x94c3cf8e36f7c87a9ce03d54009c920076ec855cd3c2714c2de92e74deb3ffb9",
            data="0x0000000000000000000000000000000000000000000000000000000000000040bce052cf723dca06a21bd3cf838bc518931730fb3db7859fc9cc86f0d5483495000000000000000000000000000000000000000000000000000000000000000500000000000000000000000000000000000000000000000000000000000000006a170eb00000000000000000000000007530d4b90b774ee2b99621f6d1f8ce304588a94200000000000000000000000000000000000000000000000000000000075bcd1510a26f912b7ebcefe8f2f6fc4d0ac9186814a7f37e90ea63c014aa256b677dfe0040b8810cbaed9647b54d18cc98b720e1e8876be5d8e7089d3c079fc61c30a4",
            decoded_data_json='[{"name":"publicValues","type":"uint256[]","signature":"uint256[] publicValues","value":{"name":"publicValues","type":"uint256[]","value":[{"type":"BigNumber","hex":"0x6a170eb0"},{"type":"BigNumber","hex":"0x7530d4b90b774ee2b99621f6d1f8ce304588a942"},{"type":"BigNumber","hex":"0x075bcd15"},{"type":"BigNumber","hex":"0x10a26f912b7ebcefe8f2f6fc4d0ac9186814a7f37e90ea63c014aa256b677dfe"},{"type":"BigNumber","hex":"0x40b8810cbaed9647b54d18cc98b720e1e8876be5d8e7089d3c079fc61c30a4"}]}},{"name":"circuitId","type":"uint256","signature":"uint256 circuitId","value":{"name":"circuitId","type":"uint256","value":{"type":"BigNumber","hex":"0xbce052cf723dca06a21bd3cf838bc518931730fb3db7859fc9cc86f0d5483495"}}}]',
            recipient="0x7530d4b90b774ee2b99621f6d1f8ce304588a942",
            attester="0xb1f50c6c34c72346b1229e5c80587d0d659556fd",
            time=1748738241,
            time_created=1748738244,
            expiration_time=1779895984,
            revocation_time=0,
            ref_uid="0x0000000000000000000000000000000000000000000000000000000000000000",
            schema_id="0xba837f9d5f2fe6bc40ffe1f4568af2e516eeebffcf276a04dbe36306780e4f4f",
            ipfs_hash="",
            is_offchain=False,
        ),
    ],
)
