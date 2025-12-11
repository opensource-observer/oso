from datetime import datetime

from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class SbomRelationship(BaseModel):
    artifact_namespace: str | None = Column("VARCHAR")
    artifact_name: str | None = Column("VARCHAR")
    artifact_source: str | None = Column("VARCHAR")
    relationship_type: str | None = Column("VARCHAR")
    spdx_element_id: str | None = Column("VARCHAR")
    related_spdx_element: str | None = Column("VARCHAR")
    snapshot_at: datetime | None = Column("TIMESTAMP(6) WITH TIME ZONE")
    dlt_load_id: str = Column("VARCHAR", column_name="_dlt_load_id")
    dlt_id: str = Column("VARCHAR", column_name="_dlt_id")


seed = SeedConfig(
    catalog="bigquery",
    schema="ossd",
    table="sbom_relationships",
    base=SbomRelationship,
    rows=[
        SbomRelationship(
            artifact_namespace="flowstake",
            artifact_name="testing",
            artifact_source="GITHUB",
            relationship_type="DESCRIBES",
            spdx_element_id="SPDXRef-DOCUMENT",
            related_spdx_element="SPDXRef-github-flowstake-testing-main-5a4321",
            snapshot_at=datetime(2025, 5, 30, 16, 1, 53),
            dlt_load_id="1748620912.519714",
            dlt_id="kUWUcHtxm2xxtQ",
        ),
        SbomRelationship(
            artifact_namespace="CommonsHub",
            artifact_name="googlereviews-bot",
            artifact_source="GITHUB",
            relationship_type="DESCRIBES",
            spdx_element_id="SPDXRef-DOCUMENT",
            related_spdx_element="SPDXRef-github-CommonsHub-googlereviews-bot-main-df63ac",
            snapshot_at=datetime(2025, 5, 30, 16, 1, 53),
            dlt_load_id="1748620912.519714",
            dlt_id="QnAAikMVfS7FQA",
        ),
        SbomRelationship(
            artifact_namespace="etherfi-protocol",
            artifact_name="Native-Minting-Bot",
            artifact_source="GITHUB",
            relationship_type="DESCRIBES",
            spdx_element_id="SPDXRef-DOCUMENT",
            related_spdx_element="SPDXRef-github-etherfi-protocol-Native-Minting-Bot-master-9b1c1f",
            snapshot_at=datetime(2025, 5, 30, 16, 1, 53),
            dlt_load_id="1748620912.519714",
            dlt_id="FGF8Wus+A6/0aQ",
        ),
        SbomRelationship(
            artifact_namespace="vegaprotocol",
            artifact_name="bounties",
            artifact_source="GITHUB",
            relationship_type="DESCRIBES",
            spdx_element_id="SPDXRef-DOCUMENT",
            related_spdx_element="SPDXRef-github-vegaprotocol-bounties-main-cb1741",
            snapshot_at=datetime(2025, 5, 30, 16, 1, 53),
            dlt_load_id="1748620912.519714",
            dlt_id="a9ISZA1c9jQlVA",
        ),
        SbomRelationship(
            artifact_namespace="verifier-alliance",
            artifact_name=".github",
            artifact_source="GITHUB",
            relationship_type="DESCRIBES",
            spdx_element_id="SPDXRef-DOCUMENT",
            related_spdx_element="SPDXRef-github-verifier-alliance-.github-main-259bd2",
            snapshot_at=datetime(2025, 5, 30, 16, 1, 53),
            dlt_load_id="1748620912.519714",
            dlt_id="K8mhyQmEl7XQaw",
        ),
    ],
)
