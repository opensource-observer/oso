from metrics_tools.seed.types import Column, SeedConfig
from pydantic import BaseModel


class CanonicalDevelopers(BaseModel):
    """Seed model for opendevdata canonical_developers"""

    id: int | None = Column("BIGINT", description="id")
    primary_developer_email_identity_id: int | None = Column(
        "BIGINT", description="primary developer email identity id"
    )
    primary_github_user_id: str | None = Column(
        "VARCHAR", description="primary github user id"
    )


seed = SeedConfig(
    catalog="bigquery",
    schema="opendevdata",
    table="canonical_developers",
    base=CanonicalDevelopers,
    rows=[
        CanonicalDevelopers(
            id=1903590,
            primary_developer_email_identity_id=2892476,
            primary_github_user_id="U_kgDOArDpjQ",
        ),
        CanonicalDevelopers(
            id=1903585,
            primary_developer_email_identity_id=2892470,
            primary_github_user_id="U_kgDOBEsEwQ",
        ),
        CanonicalDevelopers(
            id=1903531,
            primary_developer_email_identity_id=2892415,
            primary_github_user_id="U_kgDOAGMZyw",
        ),
        CanonicalDevelopers(
            id=1903603,
            primary_developer_email_identity_id=1168308,
            primary_github_user_id="U_kgDOBHN6gQ",
        ),
        CanonicalDevelopers(
            id=1903602,
            primary_developer_email_identity_id=1168079,
            primary_github_user_id="MDQ6VXNlcjEyMjYyOTQ2",
        ),
    ],
)
