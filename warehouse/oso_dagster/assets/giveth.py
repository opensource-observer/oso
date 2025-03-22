from ..factories.graphql import (
    GraphQLResourceConfig,
    graphql_factory,
)

configs = [
    GraphQLResourceConfig(
        name="all_projects",
        endpoint="https://mainnet.serve.giveth.io/graphql",
        max_depth=3,
        parameters={
            "skip": {"type": "Int", "value": 0},
            "take": {"type": "Int", "value": 50},
            "orderBy": {
                "type": "OrderByInput",
                "value": {
                    "field": "CreationDate",
                    "direction": "DESC"
                }
            }
        },
        target_query="allProjects",
        target_type="AllProjects",
        transform_fn=lambda result: result["projects"]
    ),
    GraphQLResourceConfig(
        name="donations",
        endpoint="https://mainnet.serve.giveth.io/graphql",
        max_depth=3,
        parameters={},
        target_query="donations",
        target_type="Donation",
        transform_fn=lambda result: result["donations"]
    ),
    GraphQLResourceConfig(
        name="qf_rounds",
        endpoint="https://mainnet.serve.giveth.io/graphql",
        max_depth=2,
        parameters={"activeOnly": {"type": "Boolean", "value": True}},
        target_query="qfRounds",
        target_type="QfRound",
        transform_fn=lambda result: result["qfRounds"]
    ),
    GraphQLResourceConfig(
        name="categories",
        endpoint="https://mainnet.serve.giveth.io/graphql",
        max_depth=1,
        parameters={},
        target_query="categories",
        target_type="Category",
        transform_fn=lambda result: result["categories"]
    ),
    GraphQLResourceConfig(
        name="campaigns",
        endpoint="https://mainnet.serve.giveth.io/graphql",
        max_depth=2,
        parameters={},
        target_query="campaigns",
        target_type="Campaign",
        transform_fn=lambda result: result["campaigns"]
    ),
    GraphQLResourceConfig(
        name="all_users",
        endpoint="https://mainnet.serve.giveth.io/graphql",
        max_depth=2,
        parameters={
            "skip": {"type": "Int", "value": 0},
            "limit": {"type": "Int", "value": 50}
        },
        target_query="allUsersBasicData",
        target_type="AllUsersPublicData",
        transform_fn=lambda result: result["users"]
    ),
]

giveth_assets = [graphql_factory(config, key_prefix="giveth") for config in configs]
