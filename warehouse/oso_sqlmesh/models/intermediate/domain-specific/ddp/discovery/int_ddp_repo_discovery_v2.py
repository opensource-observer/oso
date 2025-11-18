"""
SQLMesh Python model for repo discovery trust scores using NetworkX PageRank.

This model is a more sophisticated variant of the v1 discovery algorithm:
it constructs a bipartite repo↔developer graph and runs personalized
PageRank, seeding the teleport probability with pre‑trusted repo scores.
"""

from __future__ import annotations

import typing as t

import networkx as nx
import pandas as pd
from sqlmesh import ExecutionContext, model


def _discover_repos_df(context: ExecutionContext) -> pd.DataFrame:
    """
    Calculate repository trust scores using a personalized PageRank algorithm.

    The graph is bipartite:
    - Repo nodes: prefixed with \"repo:\" and keyed by repo_artifact_id
    - Developer nodes: prefixed with \"dev:\" and keyed by git_user

    Edges are added in both directions between repos and developers with
    weights based on normalized interaction strength. Pre‑trusted repos
    define the personalization vector for PageRank.
    """
    # --- 1. Fetch initial data ---
    pretrust_table = context.resolve_table("oso.int_ddp_repo_pretrust")
    graph_table = context.resolve_table("oso.int_ddp_repo_to_dev_graph")
    artifacts_table = context.resolve_table("oso.int_artifacts__github")

    pretrust_df = context.fetchdf(
        f"""
        SELECT
            repo_artifact_id,
            url,
            score AS repo_score_base
        FROM {pretrust_table}
        """
    )

    edges_raw_df = context.fetchdf(
        f"""
        SELECT
            git_user,
            repo_artifact_id,
            edge_weight
        FROM {graph_table}
        """
    )

    artifacts_df = context.fetchdf(
        f"""
        SELECT
            artifact_id,
            artifact_url AS url
        FROM {artifacts_table}
        """
    )

    if edges_raw_df.empty:
        return pd.DataFrame(
            columns=[
                "repo_artifact_id",
                "url",
                "is_pretrust",
                "base_score",
                "dev_contrib_v1",
                "dev_contrib_v2",
                "final_score",
                "delta_score",
                "trust_rank",
            ]
        )

    # --- 2. Prepare base dataframes (align with v1 shape) ---
    edges_raw_df = edges_raw_df.dropna(subset=["git_user", "repo_artifact_id"])

    # Ensure repo ids are treated as strings consistently
    edges_raw_df["repo_artifact_id"] = edges_raw_df["repo_artifact_id"].astype(str)
    if not pretrust_df.empty:
        pretrust_df["repo_artifact_id"] = pretrust_df["repo_artifact_id"].astype(str)

    combined_repo_ids = pd.concat(
        [
            edges_raw_df["repo_artifact_id"],
            pretrust_df.get("repo_artifact_id", pd.Series(dtype=str)),
        ],
        ignore_index=True,
    )
    all_repos_df = (
        pd.DataFrame(combined_repo_ids, columns=["repo_artifact_id"])
        .drop_duplicates()
        .reset_index(drop=True)
    )

    repo_base_df = pd.merge(
        all_repos_df,
        pretrust_df[["repo_artifact_id", "repo_score_base"]]
        if not pretrust_df.empty
        else pd.DataFrame(columns=["repo_artifact_id", "repo_score_base"]),
        on="repo_artifact_id",
        how="left",
    )
    repo_base_df["repo_score_base"] = repo_base_df["repo_score_base"].fillna(0.0)
    repo_base_df["is_pretrust"] = repo_base_df["repo_artifact_id"].isin(
        pretrust_df["repo_artifact_id"] if not pretrust_df.empty else []
    )

    # Normalize outgoing edges per developer (same as v1)
    dev_edge_sum = edges_raw_df.groupby("git_user")["edge_weight"].transform("sum")
    edges_norm_df = edges_raw_df.copy()
    edges_norm_df["edge_weight_norm"] = edges_raw_df["edge_weight"] / dev_edge_sum
    edges_norm_df = edges_norm_df.fillna(0)

    # --- 3. Build bipartite graph and personalization vector ---
    G = nx.DiGraph()

    # Add repo and dev nodes
    for repo_id in repo_base_df["repo_artifact_id"].unique():
        G.add_node(f"repo:{repo_id}", kind="repo")
    for dev in edges_norm_df["git_user"].dropna().unique():
        G.add_node(f"dev:{dev}", kind="dev")

    # Add bidirectional edges between repos and devs
    for _, row in edges_norm_df.iterrows():
        repo_id = str(row["repo_artifact_id"])
        dev = row["git_user"]
        w = float(row.get("edge_weight_norm", 0.0) or 0.0)
        if not dev or w <= 0:
            continue
        repo_node = f"repo:{repo_id}"
        dev_node = f"dev:{dev}"
        # repo -> dev and dev -> repo to allow random walks to move across the bipartite graph
        G.add_edge(repo_node, dev_node, weight=w)
        G.add_edge(dev_node, repo_node, weight=w)

    # Personalization: bias teleportation to pre‑trusted repos using their base scores
    personalization: dict[str, float] = {}
    base_scores = repo_base_df.set_index("repo_artifact_id")["repo_score_base"]
    base_sum = float(base_scores.sum())

    if base_sum > 0:
        for repo_id, score in base_scores.items():
            node = f"repo:{repo_id}"
            personalization[node] = float(score) / base_sum
    else:
        # Fallback: uniform over repos if no pretrust scores
        repo_ids = list(repo_base_df["repo_artifact_id"].unique())
        if repo_ids:
            uniform = 1.0 / len(repo_ids)
            for repo_id in repo_ids:
                personalization[f"repo:{repo_id}"] = uniform

    # Ensure all nodes have some personalization mass (NetworkX requirement)
    if personalization:
        for node in G.nodes:
            personalization.setdefault(node, 0.0)

    if not G.nodes:
        return pd.DataFrame(
            columns=[
                "repo_artifact_id",
                "url",
                "is_pretrust",
                "base_score",
                "dev_contrib_v1",
                "dev_contrib_v2",
                "final_score",
                "delta_score",
                "trust_rank",
            ]
        )

    # --- 4. Run personalized PageRank ---
    try:
        pr_scores = nx.pagerank(
            G,
            alpha=0.85,
            personalization=personalization or None,
            weight="weight",
            max_iter=100,
            tol=1.0e-06,
        )
    except nx.PowerIterationFailedConvergence:
        # Fallback: treat all repos as equal if PageRank fails to converge
        n_repos = len(repo_base_df)
        equal_score = 1.0 / n_repos if n_repos > 0 else 0.0
        pr_scores = {
            f"repo:{rid}": equal_score for rid in repo_base_df["repo_artifact_id"]
        }

    # --- 5. Build result DataFrame ---
    repo_scores = []
    for _, row in repo_base_df.iterrows():
        repo_id = row["repo_artifact_id"]
        node = f"repo:{repo_id}"
        final_score = float(pr_scores.get(node, 0.0))
        base_score = float(row["repo_score_base"])
        is_pretrust = bool(row["is_pretrust"])
        repo_scores.append(
            {
                "repo_artifact_id": repo_id,
                "is_pretrust": is_pretrust,
                "base_score": base_score,
                # No direct analogs for single-iteration dev contributions in PageRank;
                # keep columns for compatibility and fill with 0.0.
                "dev_contrib_v1": 0.0,
                "dev_contrib_v2": 0.0,
                "final_score": final_score,
            }
        )

    repo_scores_df = pd.DataFrame(repo_scores)

    # Join artifact URLs
    if not artifacts_df.empty:
        artifacts_df = artifacts_df.copy()
        artifacts_df["artifact_id"] = artifacts_df["artifact_id"].astype(str)
        final_df = pd.merge(
            repo_scores_df,
            artifacts_df,
            left_on="repo_artifact_id",
            right_on="artifact_id",
            how="left",
        )
    else:
        final_df = repo_scores_df.copy()
        final_df["artifact_id"] = pd.NA
        final_df["url"] = pd.NA

    # Delta score and trust rank
    final_df["delta_score"] = final_df["final_score"] - final_df["base_score"]
    final_df["trust_rank"] = (
        final_df["final_score"].rank(method="min", ascending=False).astype(int)
    )

    output_df = final_df[
        [
            "repo_artifact_id",
            "url",
            "is_pretrust",
            "base_score",
            "dev_contrib_v1",
            "dev_contrib_v2",
            "final_score",
            "delta_score",
            "trust_rank",
        ]
    ].copy()

    # Stable ordering by final score
    output_df = output_df.sort_values(by="final_score", ascending=False).reset_index(
        drop=True
    )

    return output_df


@model(
    "oso.int_ddp_repo_discovery_v2",
    kind="full",
    columns={
        "repo_artifact_id": "TEXT",
        "url": "TEXT",
        "is_pretrust": "BOOLEAN",
        "base_score": "DOUBLE",
        "dev_contrib_v1": "DOUBLE",
        "dev_contrib_v2": "DOUBLE",
        "final_score": "DOUBLE",
        "delta_score": "DOUBLE",
        "trust_rank": "INTEGER",
    },
    grain=("repo_artifact_id",),
    enabled=False,
    audits=[
        ("has_at_least_n_rows", {"threshold": 0}),
    ],
)
def execute(
    context: ExecutionContext,
    start: t.Optional[str] = None,
    end: t.Optional[str] = None,
    execution_time: t.Optional[str] = None,
    **kwargs: t.Any,
) -> t.Iterator[pd.DataFrame]:
    """
    SQLMesh model entrypoint for the PageRank-based repo discovery algorithm.

    This is a FULL model (no incremental windowing). The optional `start` and
    `end` parameters are accepted for signature compatibility with other
    models but are not used.
    """
    df = _discover_repos_df(context)
    if df.empty:
        yield from ()
        return

    ordered = df[
        [
            "repo_artifact_id",
            "url",
            "is_pretrust",
            "base_score",
            "dev_contrib_v1",
            "dev_contrib_v2",
            "final_score",
            "delta_score",
            "trust_rank",
        ]
    ].copy()
    yield ordered  # type: ignore[misc]
