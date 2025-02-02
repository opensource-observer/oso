import typing as t
from datetime import datetime

import pandas as pd
from openrank_sdk import EigenTrust
from sqlmesh import ExecutionContext, model
from sqlmesh.core.dialect import parse_one


# simple illustration of a weighting function
def weight_contributions(bucket_month, amount):
    year = bucket_month.year
    weight = ((2018 - year) / 4) * (amount**0.5)
    return weight


# another simple illustration of a weighting function
def weight_events(event_type, amount):
    weight = (amount**0.5) * (0.5 if event_type == "STARRED" else 1.0)
    return weight


@model(
    "metrics.int_openrank_developer",
    kind="full",
    depends_on=[
        "metrics.int_artifacts",
        "metrics.int_events_monthly_to_project",
    ],
    columns={
        # "id": "int",
        "i": "text",
        "v": "float",
    },
    column_descriptions={
        "i": "Developer GitHub handle",
        "v": "OpenRank reputation score",
    },
    audits=[
        ("not_null", {"columns": ["i", "v"]}),
    ],
)
def execute(
    context: ExecutionContext,
    start: datetime,
    end: datetime,
    execution_time: datetime,
    **kwargs: t.Any,
) -> t.Iterator[pd.DataFrame]:
    artifacts_table = context.resolve_table("metrics.int_artifacts")
    events_table = context.resolve_table("metrics.int_events_monthly_to_project")

    # Get trusted developers
    seeded_developers_query = parse_one(
        f"""
        with targeted_repos as (
            select
                artifact_id,
                artifact_namespace,
                artifact_name
            from {artifacts_table}
            where CONCAT(artifact_source, artifact_namespace, artifact_name) in (
                CONCAT('GITHUB', 'ethereum', 'eips'),
                CONCAT('GITHUB', 'ethereum', 'solidity'),
                CONCAT('GITHUB', 'ethereum', 'go-ethereum'),
            )
        )
        
        select
            a.artifact_name as user,
            targeted_repos.artifact_name as repo,
            e.event_type,
            e.bucket_month,
            e.amount
        from {events_table} e
        join {artifacts_table} a
            on e.from_artifact_id = a.artifact_id
        join targeted_repos
            on e.to_artifact_id = targeted_repos.artifact_id
        where
            e.event_type = 'COMMIT_CODE'
            and e.bucket_month > date '2014-01-01'
            and e.to_artifact_id in (
                select artifact_id
                from targeted_repos
            )
    """,
        dialect="duckdb",
    )
    seeded_developers = context.fetchdf(seeded_developers_query.sql(dialect="trino"))
    if seeded_developers.empty:
        yield from ()
        return

    # Generate pretrust values
    seeded_developers["v"] = seeded_developers.apply(
        lambda x: weight_contributions(x["bucket_month"], x["amount"]), axis=1
    )
    pretrust = []
    developers = []
    for i, v in seeded_developers.groupby("user")["v"].sum().items():
        pretrust.append({"i": i, "v": v})
        developers.append(i)

    # Get trusted repos
    developers_str = "'" + "','".join(developers) + "'"
    trusted_repos_query = f"""
        with trusted_repos as (
            select
                e.to_artifact_id as artifact_id,
                users.artifact_name as trusted_user,
                e.event_type as trusted_event
            from {events_table} e
            join {artifacts_table} users
                on e.from_artifact_id = users.artifact_id
            where
                e.event_type in ('STARRED', 'FORKED')
                and e.bucket_month > date '2022-01-01'
                and users.artifact_name in ({developers_str})
        )
        
        select
            trusted_repos.trusted_user,
            trusted_repos.trusted_event,
            users.artifact_name as github_user,
            repos.artifact_namespace as github_org,
            repos.artifact_name as github_repo,
            e.event_type,
            e.bucket_month,
            e.amount
        from {events_table} e
        join {artifacts_table} users
            on e.from_artifact_id = users.artifact_id
        join trusted_repos
            on e.to_artifact_id = trusted_repos.artifact_id
        join {artifacts_table} repos
            on e.to_artifact_id = repos.artifact_id
        where
            e.event_type = 'COMMIT_CODE'
            and e.bucket_month > date '2022-01-01'
    """
    trusted_repos = context.fetchdf(trusted_repos_query)
    if trusted_repos.empty:
        yield from ()
        return

    # Construct a graph from the event data
    trusted_repos["v"] = trusted_repos.apply(
        lambda x: weight_events(x["event_type"], x["amount"]), axis=1
    )
    localtrust = []
    for item in (
        trusted_repos.groupby(["trusted_user", "github_user"])["v"].sum().items()
    ):
        # ((i, j), v) = item
        k = t.cast(t.Tuple[str, str], item[0])
        i, j = k
        v = float(item[1])
        if i == j or "[bot]" in j:
            continue
        localtrust.append({"i": i, "j": j, "v": v})

    # Run EigenTrust over the graph
    pretrust_updated = [
        x for x in pretrust if x["i"] in trusted_repos["trusted_user"].unique()
    ]
    a = EigenTrust()
    dev_rank = a.run_eigentrust(localtrust, pretrust_updated)

    # Return the results
    df = pd.DataFrame(dev_rank)
    if df.empty:
        yield from ()
    else:
        yield df
