from ..factories.graphql import GraphQLResourceConfig, graphql_factory

configs = [
    GraphQLResourceConfig(
        name="all_projects",
        endpoint="https://mainnet.serve.giveth.io/graphql",
        max_depth=1,
        parameters={
            "qfRoundId": {"type": "Int", "value": 12},  # Dynamically templated later
            "skip": {"type": "Int", "value": 0},
            "take": {"type": "Int", "value": 50},
            "orderBy": {
                "type": "OrderBy",
                "value": {
                    "field": "CreationDate",
                    "direction": "DESC"
                }
            }
        },
        target_query="allProjects",
        target_type="AllProjects",      
        transform_fn=lambda result: result["allProjects"]["projects"]
    ),
    GraphQLResourceConfig(
        name="qf_rounds",
        endpoint="https://mainnet.serve.giveth.io/graphql",
        max_depth=2,
        parameters={"activeOnly": {"type": "Boolean", "value": False}},
        target_query="qfRounds",
        target_type="QfRound",
        transform_fn=lambda result: result["qfRounds"]
    ),
]

giveth_assets = [graphql_factory(config, key_prefix="giveth") for config in configs]