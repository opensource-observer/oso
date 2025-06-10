import polars as pl
from dagster import multi_asset, AssetOut, Output
from ..factories.graphql import GraphQLResourceConfig, PaginationConfig, PaginationType, graphql_factory
from metrics_service.types import AppConfig  # Needed for `global_config`

@multi_asset(
    outs={
        "giveth__qf_rounds_v3": AssetOut(),
        "giveth__projects_by_round_v3": AssetOut(),
    },
)
def fetch_giveth_data():
    endpoint = "https://mainnet.serve.giveth.io/graphql"
    config = AppConfig()  # Load default config required by factory

    qf_rounds_config = GraphQLResourceConfig(
        name="giveth_qf_rounds",
        endpoint=endpoint,
        target_type="Query",
        target_query="qfRounds(activeOnly: $activeOnly)",
        parameters={"activeOnly": {"type": "Boolean!", "value": False}},
    )

    projects_pagination = PaginationConfig(
        type=PaginationType.OFFSET,
        page_size=50,
        offset_field="skip",
        limit_field="take",
        total_count_path="allProjects.totalCount"
    )

    projects_config = GraphQLResourceConfig(
        name="giveth_projects",
        endpoint=endpoint,
        target_type="Query",
        target_query="allProjects(qfRoundId: $qfRoundId, skip: $skip, take: $take, orderBy: $orderBy)",
        pagination=projects_pagination,
        parameters={
            "qfRoundId": {"type": "Int!", "value": 0},
            "skip": {"type": "Int!", "value": 0},
            "take": {"type": "Int!", "value": 50},
            "orderBy": {
                "type": "OrderByInput",
                "value": {"field": "CreationDate", "direction": "DESC"},
            },
        },
    )

    # Fetch QF rounds
    get_qf_rounds = graphql_factory(qf_rounds_config)
    qf_rounds_resource = get_qf_rounds(global_config=config, dependencies={})
    qf_rounds_data = list(qf_rounds_resource)
    qf_rounds_df = pl.DataFrame(qf_rounds_data)

    print("QF Rounds DF schema:", qf_rounds_df.schema)
    print(qf_rounds_df.head(3))
    yield Output(qf_rounds_df, output_name="giveth__qf_rounds_v3")

    # Fetch projects per round
    all_projects = []
    for round_data in qf_rounds_data:
        round_id = round_data["id"]
        projects_config.parameters["qfRoundId"]["value"] = round_id

        get_projects_per_round = graphql_factory(projects_config)
        projects_resource = get_projects_per_round(global_config=config, dependencies={})
        projects_data = list(projects_resource)
        all_projects.extend(projects_data)

    projects_df = pl.DataFrame(all_projects)
    print("Projects DF schema:", projects_df.schema)
    print(projects_df.head(3))
    yield Output(projects_df, output_name="giveth__projects_by_round_v3")
