import textwrap

from ..definition import (
    Dimension,
    Measure,
    Model,
    Registry,
    Relationship,
    RelationshipType,
)


def register_entities(registry: Registry, catalog_name: str = "iceberg"):
    # ============================================"
    # CORE ENTITIES
    # ============================================"

    registry.register(
        Model(
            name="artifacts",
            table=f"{catalog_name}.oso.artifacts_v1",
            description=textwrap.dedent(
                """
                An artifact. This is the smallest atom of an acting entity in
                OSO. Artifacts are usually repositories, blockchain addresses,
                or some representation of a user. Artifacts do not generally
                represent a group of any kind, but rather a single entity.
                """
            ),
            dimensions=[
                Dimension(
                    name="artifact_id",
                    description="The unique identifier for the artifact",
                    column_name="artifact_id",
                ),
                Dimension(
                    name="artifact_source_id",
                    description="The native identifier for the artifact from the source, such as a GitHub repository ID or NPM package ID",
                    column_name="artifact_source_id",
                ),
                Dimension(
                    name="artifact_source",
                    description='The original source of the artifact, such as "GITHUB", "NPM", or "DEFILLAMA"',
                    column_name="artifact_source",
                ),
                Dimension(
                    name="artifact_namespace",
                    description="The grouping or namespace of the artifact, such as the GitHub organization or NPM scope. It will will be empty if the artifact source does not have its own namespacing conventions",
                    column_name="artifact_namespace",
                ),
                Dimension(
                    name="artifact_name",
                    description="The name of the artifact, such as the GitHub repository name, NPM package name, or blockchain address",
                    column_name="artifact_name",
                ),
            ],
            primary_key="artifact_id",
            relationships=[
                Relationship(
                    name="by_project",
                    source_foreign_key="artifact_id",
                    ref_model="artifacts_by_project",
                    ref_key="artifact_id",
                    type=RelationshipType.ONE_TO_MANY,
                ),
                Relationship(
                    name="by_collection",
                    source_foreign_key="artifact_id",
                    ref_model="artifacts_by_collection",
                    ref_key="artifact_id",
                    type=RelationshipType.ONE_TO_MANY,
                ),
            ],
            measures=[
                Measure(
                    name="count",
                    description="The number of artifacts",
                    query="COUNT(self.artifact_id)",
                ),
                Measure(
                    name="distinct_count",
                    description="The number of distinct artifacts",
                    query="COUNT(DISTINCT self.artifact_id)",
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="projects",
            table=f"{catalog_name}.oso.projects_v1",
            description=textwrap.dedent(
                """
                A project is a collection of related artifacts. A project is
                usually, but not limited to, some kind of organization, company,
                or group that controls a set of artifacts.
                """
            ),
            dimensions=[
                Dimension(
                    name="project_id",
                    description="The unique identifier for the project, as generated by OSO",
                    column_name="project_id",
                ),
                Dimension(
                    name="project_source",
                    description='The source of the project, such as "OSS_DIRECTORY", or "OP_ATLAS"',
                    column_name="project_source",
                ),
                Dimension(
                    name="project_namespace",
                    description="The namespace of the project within the source, which may include organization information",
                    column_name="project_namespace",
                ),
                Dimension(
                    name="project_name",
                    description="the project slug or other name given to the project (unique to the registry but not globally unique)",
                    column_name="project_name",
                ),
                Dimension(
                    name="display_name",
                    description="The display name of the project, which may be a more human-readable name than the project_name",
                    column_name="display_name",
                ),
                Dimension(
                    name="description",
                    description="A short description of the project",
                    column_name="description",
                ),
            ],
            primary_key="project_id",
            relationships=[
                Relationship(
                    name="by_collection",
                    source_foreign_key="project_id",
                    ref_model="projects_by_collection",
                    ref_key="project_id",
                    type=RelationshipType.ONE_TO_MANY,
                ),
            ],
            measures=[
                Measure(
                    name="count",
                    description="The number of projects",
                    query="COUNT(self.project_id)",
                ),
                Measure(
                    name="distinct_count",
                    description="The number of distinct projects",
                    query="COUNT(DISTINCT self.project_id)",
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="collections",
            table=f"{catalog_name}.oso.collections_v1",
            description=textwrap.dedent(
                """
                A collection is a group of related projects. A collection is an
                arbitrary grouping of projects. Sometimes these groupings are
                used to group things together by some common dependency tree or
                some specific community known to OSO.
                """
            ),
            dimensions=[
                Dimension(
                    name="collection_id",
                    description="The unique identifier for the collection",
                    column_name="collection_id",
                ),
                Dimension(
                    name="collection_source",
                    description='The source of the collection, such as "OP_ATLAS" or "OSS_DIRECTORY"',
                    column_name="collection_source",
                ),
                Dimension(
                    name="collection_namespace",
                    description="The grouping or namespace of the collection",
                    column_name="collection_namespace",
                ),
                Dimension(
                    name="collection_name",
                    description="The name of the collection, such as an ecosystem name. If the collections are from OSS_DIRECTORY, this will be a unique collection slug",
                    column_name="collection_name",
                ),
                Dimension(
                    name="display_name",
                    description="The display name of the collection, which may not be unique. This is typically a human-readable name",
                    column_name="display_name",
                ),
                Dimension(
                    name="description",
                    description="brief summary or purpose of the collection",
                    column_name="description",
                ),
            ],
            primary_key="collection_id",
            measures=[
                Measure(
                    name="count",
                    description="The number of collections",
                    query="COUNT(self.collection_id)",
                ),
                Measure(
                    name="distinct_count",
                    description="The number of distinct collections",
                    query="COUNT(DISTINCT self.collection_id)",
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="contracts",
            table=f"{catalog_name}.oso.contracts_v0",
            description=textwrap.dedent(
                """
                This table contains information about smart contracts deployed across 
                various blockchain networks, including deployment details and relationships.
                """
            ),
            dimensions=[
                Dimension(
                    name="deployment_date",
                    description="The date of a contract deployment",
                    column_name="deployment_date",
                ),
                Dimension(
                    name="contract_address",
                    description="The address of the contract",
                    column_name="contract_address",
                ),
                Dimension(
                    name="contract_namespace",
                    description="The chain of the contract",
                    column_name="contract_namespace",
                ),
                Dimension(
                    name="originating_address",
                    description="The EOA address that initiated the contract deployment transaction",
                    column_name="originating_address",
                ),
                Dimension(
                    name="factory_address",
                    description="The address of the factory that deployed the contract, if this is the same as the originating address then this was a direct deployment by an EOA",
                    column_name="factory_address",
                ),
                Dimension(
                    name="root_deployer_address",
                    description="The EOA address that is considered the root deployer of the contract. If the contract was deployed directly by an EOA, this should be the same as the originating address, if the contract was deployed by a factory this is the creator of the factory",
                    column_name="root_deployer_address",
                ),
                Dimension(
                    name="sort_weight",
                    description="A weight used for sorting contracts. At this time, this is the tx count of the last 180 days",
                    column_name="sort_weight",
                ),
            ],
            primary_key="contract_address",
            measures=[
                Measure(
                    name="count",
                    description="The number of contracts",
                    query="COUNT(self.contract_address)",
                ),
                Measure(
                    name="distinct_count",
                    description="The number of distinct contracts",
                    query="COUNT(DISTINCT self.contract_address)",
                ),
                Measure(
                    name="avg_sort_weight",
                    description="The average sort weight of contracts",
                    query="AVG(self.sort_weight)",
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="repositories",
            table=f"{catalog_name}.oso.repositories_v0",
            description=textwrap.dedent(
                """
                This table contains information about source code repositories,
                primarily from GitHub, including repository metadata and statistics.
                """
            ),
            dimensions=[
                Dimension(
                    name="artifact_id",
                    description="The unique identifier for the artifact",
                    column_name="artifact_id",
                ),
                Dimension(
                    name="artifact_source_id",
                    description="The native identifier for the artifact from the source",
                    column_name="artifact_source_id",
                ),
                Dimension(
                    name="artifact_source",
                    description="The original source of the artifact",
                    column_name="artifact_source",
                ),
                Dimension(
                    name="artifact_namespace",
                    description="The grouping or namespace of the artifact",
                    column_name="artifact_namespace",
                ),
                Dimension(
                    name="artifact_name",
                    description="The name of the artifact",
                    column_name="artifact_name",
                ),
                Dimension(
                    name="artifact_url",
                    description="The URL of the repository",
                    column_name="artifact_url",
                ),
                Dimension(
                    name="is_fork",
                    description="Whether the repository is a fork",
                    column_name="is_fork",
                ),
                Dimension(
                    name="branch",
                    description="The default branch of the repository",
                    column_name="branch",
                ),
                Dimension(
                    name="star_count",
                    description="The number of stars for the repository",
                    column_name="star_count",
                ),
                Dimension(
                    name="watcher_count",
                    description="The number of watchers for the repository",
                    column_name="watcher_count",
                ),
                Dimension(
                    name="fork_count",
                    description="The number of forks for the repository",
                    column_name="fork_count",
                ),
                Dimension(
                    name="license_name",
                    description="The name of the license",
                    column_name="license_name",
                ),
                Dimension(
                    name="license_spdx_id",
                    description="The SPDX ID of the license",
                    column_name="license_spdx_id",
                ),
                Dimension(
                    name="language",
                    description="The primary programming language of the repository",
                    column_name="language",
                ),
                Dimension(
                    name="created_at",
                    description="The timestamp when the repository was created",
                    column_name="created_at",
                ),
                Dimension(
                    name="updated_at",
                    description="The timestamp when the repository was last updated",
                    column_name="updated_at",
                ),
            ],
            primary_key="artifact_id",
            measures=[
                Measure(
                    name="count",
                    description="The number of repositories",
                    query="COUNT(*)",
                ),
                Measure(
                    name="total_stars",
                    description="The total number of stars across repositories",
                    query="SUM(self.star_count)",
                ),
                Measure(
                    name="avg_stars",
                    description="The average number of stars per repository",
                    query="AVG(self.star_count)",
                ),
                Measure(
                    name="total_forks",
                    description="The total number of forks across repositories",
                    query="SUM(self.fork_count)",
                ),
                Measure(
                    name="avg_forks",
                    description="The average number of forks per repository",
                    query="AVG(self.fork_count)",
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="package_owners",
            table=f"{catalog_name}.oso.package_owners_v0",
            description=textwrap.dedent(
                """
                This table contains information about package ownership relationships
                between packages and their owners across different package registries.
                """
            ),
            dimensions=[
                Dimension(
                    name="package_project_id",
                    description="The project ID of the package",
                    column_name="package_project_id",
                ),
                Dimension(
                    name="package_artifact_id",
                    description="The artifact ID of the package",
                    column_name="package_artifact_id",
                ),
                Dimension(
                    name="package_artifact_source",
                    description="The source of the package artifact",
                    column_name="package_artifact_source",
                ),
                Dimension(
                    name="package_artifact_namespace",
                    description="The namespace of the package artifact",
                    column_name="package_artifact_namespace",
                ),
                Dimension(
                    name="package_artifact_name",
                    description="The name of the package artifact",
                    column_name="package_artifact_name",
                ),
                Dimension(
                    name="package_owner_project_id",
                    description="The project ID of the package owner",
                    column_name="package_owner_project_id",
                ),
                Dimension(
                    name="package_owner_artifact_id",
                    description="The artifact ID of the package owner",
                    column_name="package_owner_artifact_id",
                ),
                Dimension(
                    name="package_owner_source",
                    description="The source of the package owner",
                    column_name="package_owner_source",
                ),
                Dimension(
                    name="package_owner_artifact_namespace",
                    description="The namespace of the package owner artifact",
                    column_name="package_owner_artifact_namespace",
                ),
                Dimension(
                    name="package_owner_artifact_name",
                    description="The name of the package owner artifact",
                    column_name="package_owner_artifact_name",
                ),
            ],
            primary_key=["package_artifact_id", "package_owner_artifact_id"],
            measures=[
                Measure(
                    name="count",
                    description="The number of package ownership records",
                    query="COUNT(*)",
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="sboms",
            table=f"{catalog_name}.oso.sboms_v0",
            description=textwrap.dedent(
                """
                Software Bill of Materials (SBOM) data containing information about
                software dependencies between projects and packages.
                """
            ),
            dimensions=[
                Dimension(
                    name="from_project_id",
                    description="The project ID of the dependent project",
                    column_name="from_project_id",
                ),
                Dimension(
                    name="from_artifact_id",
                    description="The artifact ID of the dependent artifact",
                    column_name="from_artifact_id",
                ),
                Dimension(
                    name="from_artifact_source",
                    description="The source of the dependent artifact",
                    column_name="from_artifact_source",
                ),
                Dimension(
                    name="from_artifact_namespace",
                    description="The namespace of the dependent artifact",
                    column_name="from_artifact_namespace",
                ),
                Dimension(
                    name="from_artifact_name",
                    description="The name of the dependent artifact",
                    column_name="from_artifact_name",
                ),
                Dimension(
                    name="to_package_project_id",
                    description="The project ID of the dependency package",
                    column_name="to_package_project_id",
                ),
                Dimension(
                    name="to_package_artifact_id",
                    description="The artifact ID of the dependency package",
                    column_name="to_package_artifact_id",
                ),
                Dimension(
                    name="to_package_artifact_source",
                    description="The source of the dependency package",
                    column_name="to_package_artifact_source",
                ),
                Dimension(
                    name="to_package_artifact_namespace",
                    description="The namespace of the dependency package",
                    column_name="to_package_artifact_namespace",
                ),
                Dimension(
                    name="to_package_artifact_name",
                    description="The name of the dependency package",
                    column_name="to_package_artifact_name",
                ),
            ],
            primary_key=["from_artifact_id", "to_package_artifact_id"],
            measures=[
                Measure(
                    name="count",
                    description="The number of SBOM dependency records",
                    query="COUNT(*)",
                ),
                Measure(
                    name="distinct_from_artifacts",
                    description="The number of distinct artifacts with dependencies",
                    query="COUNT(DISTINCT self.from_artifact_id)",
                ),
                Measure(
                    name="distinct_to_packages",
                    description="The number of distinct dependency packages",
                    query="COUNT(DISTINCT self.to_package_artifact_id)",
                ),
            ],
        )
    )

    # ============================================"
    # RELATIONSHIP TABLES
    # ============================================"

    registry.register(
        Model(
            name="artifacts_by_project",
            table=f"{catalog_name}.oso.artifacts_by_project_v1",
            description=textwrap.dedent(
                """
                The join table between artifacts and projects. This table
                represents the many-to-many relationship between artifacts and
                projects.
                """
            ),
            dimensions=[
                Dimension(
                    name="artifact_id",
                    description="The unique identifier for the artifact",
                    column_name="artifact_id",
                ),
                Dimension(
                    name="artifact_source_id",
                    description="The native identifier for the artifact from the source, such as a GitHub repository ID or NPM package ID",
                    column_name="artifact_source_id",
                ),
                Dimension(
                    name="artifact_source",
                    description='The original source of the artifact, such as "GITHUB", "NPM", or "DEFILLAMA"',
                    column_name="artifact_source",
                ),
                Dimension(
                    name="artifact_namespace",
                    description="The grouping or namespace of the artifact, such as the GitHub organization or NPM scope",
                    column_name="artifact_namespace",
                ),
                Dimension(
                    name="artifact_name",
                    description="The name of the artifact, such as the GitHub repository name, NPM package name, or blockchain address",
                    column_name="artifact_name",
                ),
                Dimension(
                    name="project_id",
                    description="The unique identifier for the project that owns the artifact",
                    column_name="project_id",
                ),
                Dimension(
                    name="project_source",
                    description='The source of the project, such as "OP_ATLAS" or "OSS_DIRECTORY"',
                    column_name="project_source",
                ),
                Dimension(
                    name="project_namespace",
                    description="The grouping or namespace of the project",
                    column_name="project_namespace",
                ),
                Dimension(
                    name="project_name",
                    description="The name of the project, such as the GitHub organization name. If the projects are from OSS_DIRECTORY, this will be a unique project slug",
                    column_name="project_name",
                ),
            ],
            primary_key=["artifact_id", "project_id"],
            relationships=[
                Relationship(
                    source_foreign_key="project_id",
                    ref_model="projects",
                    ref_key="project_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
                Relationship(
                    source_foreign_key="artifact_id",
                    ref_model="artifacts",
                    ref_key="artifact_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="projects_by_collection",
            table=f"{catalog_name}.oso.projects_by_collection_v1",
            description=textwrap.dedent(
                """
                The join table between projects and collections. This table
                represents the many-to-many relationship between projects and
                collections.
                """
            ),
            dimensions=[
                Dimension(
                    name="project_id",
                    description="The unique identifier for the project, as generated by OSO",
                    column_name="project_id",
                ),
                Dimension(
                    name="project_source",
                    description='The source of the project, such as "OSS_DIRECTORY", or "OP_ATLAS"',
                    column_name="project_source",
                ),
                Dimension(
                    name="project_namespace",
                    description="The namespace of the project within the source, which may include organization information",
                    column_name="project_namespace",
                ),
                Dimension(
                    name="project_name",
                    description="The project slug or other name given to the project (unique to the registry but not globally unique)",
                    column_name="project_name",
                ),
                Dimension(
                    name="collection_id",
                    description="The unique identifier for the collection, as generated by OSO",
                    column_name="collection_id",
                ),
                Dimension(
                    name="collection_source",
                    description='The source of the collection, such as "OSS_DIRECTORY", or "OP_ATLAS"',
                    column_name="collection_source",
                ),
                Dimension(
                    name="collection_namespace",
                    description="The namespace of the collection within the source, which may include organization information",
                    column_name="collection_namespace",
                ),
                Dimension(
                    name="collection_name",
                    description="The name of the collection",
                    column_name="collection_name",
                ),
            ],
            primary_key=["project_id", "collection_id"],
            relationships=[
                Relationship(
                    source_foreign_key="collection_id",
                    ref_model="collections",
                    ref_key="collection_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
                Relationship(
                    source_foreign_key="project_id",
                    ref_model="projects",
                    ref_key="project_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )

    registry.register(
        Model(
            name="artifacts_by_collection",
            table=f"{catalog_name}.oso.artifacts_by_collection_v1",
            description=textwrap.dedent(
                """
                The join table between artifacts and collections. This table represents 
                the many-to-many relationship between artifacts and collections.
                """
            ),
            dimensions=[
                Dimension(
                    name="artifact_id",
                    description="The unique identifier for the artifact",
                    column_name="artifact_id",
                ),
                Dimension(
                    name="artifact_source_id",
                    description="The native identifier for the artifact from the source, such as a GitHub repository ID or NPM package ID",
                    column_name="artifact_source_id",
                ),
                Dimension(
                    name="artifact_source",
                    description='The original source of the artifact, such as "GITHUB", "NPM", or "DEFILLAMA"',
                    column_name="artifact_source",
                ),
                Dimension(
                    name="artifact_namespace",
                    description="The grouping or namespace of the artifact, such as the GitHub organization or NPM scope",
                    column_name="artifact_namespace",
                ),
                Dimension(
                    name="artifact_name",
                    description="The name of the artifact, such as the GitHub repository name, NPM package name, or blockchain address",
                    column_name="artifact_name",
                ),
                Dimension(
                    name="collection_id",
                    description="The unique identifier for the collection that includes the artifact",
                    column_name="collection_id",
                ),
                Dimension(
                    name="collection_source",
                    description='The source of the collection, such as "OP_ATLAS" or "OSS_DIRECTORY"',
                    column_name="collection_source",
                ),
                Dimension(
                    name="collection_namespace",
                    description="The grouping or namespace of the collection",
                    column_name="collection_namespace",
                ),
                Dimension(
                    name="collection_name",
                    description="The name of the collection, such as an ecosystem name. If the collections are from OSS_DIRECTORY, this will be a unique collection slug",
                    column_name="collection_name",
                ),
            ],
            primary_key=["artifact_id", "collection_id"],
            relationships=[
                Relationship(
                    source_foreign_key="collection_id",
                    ref_model="collections",
                    ref_key="collection_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
                Relationship(
                    source_foreign_key="artifact_id",
                    ref_model="artifacts",
                    ref_key="artifact_id",
                    type=RelationshipType.MANY_TO_ONE,
                ),
            ],
        )
    )
