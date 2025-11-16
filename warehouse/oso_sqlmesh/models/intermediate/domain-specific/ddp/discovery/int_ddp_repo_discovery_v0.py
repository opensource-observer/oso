"""
v0 discovery algorithm for finding related repositories to Ethereum development.

This script is a Python and pandas implementation of the SQL query in
`warehouse/oso_sqlmesh/models/intermediate/domain-specific/ddp/discovery/int_ddp_repo_discovery_v0.sql`.
"""

import pandas as pd


def discover_repos(context):
    """
    Calculates repository trust scores based on a discovery algorithm.

    Args:
        context: An object with a `fetchdf` method to execute SQL queries
                 and return pandas DataFrames.

    Returns:
        A pandas DataFrame with ranked repositories and their trust scores.
    """
    # --- Configuration ---
    ALPHA = 0.5
    NUM_ITERATIONS = 2  # In the SQL, this is hardcoded to 2 iterations.

    # --- 1. Fetch initial data ---
    pretrust_df = context.fetchdf("""
        SELECT
            repo_artifact_id,
            url,
            score AS repo_score_base
        FROM oso.int_ddp_repo_pretrust
    """)

    edges_raw_df = context.fetchdf("""
        SELECT
            git_user,
            repo_artifact_id,
            edge_weight
        FROM oso.int_ddp_repo_to_dev_graph
    """)

    artifacts_df = context.fetchdf("""
        SELECT
            artifact_id,
            artifact_url AS url
        FROM oso.int_artifacts__github
    """)

    # --- 2. Prepare base dataframes ---

    # Get all unique repos from the graph and pretrust list
    combined_repo_ids = pd.concat(
        [edges_raw_df["repo_artifact_id"], pretrust_df["repo_artifact_id"]],
        ignore_index=True,
    )
    all_repos_df = (
        pd.DataFrame(combined_repo_ids, columns=["repo_artifact_id"])
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # Create base scores for all repos (0 for discovered repos)
    repo_base_df = pd.merge(
        all_repos_df,
        pretrust_df[["repo_artifact_id", "repo_score_base"]],
        on="repo_artifact_id",
        how="left",
    )
    repo_base_df["repo_score_base"] = repo_base_df["repo_score_base"].fillna(0.0)
    repo_base_df["is_pretrust"] = repo_base_df["repo_artifact_id"].isin(
        pretrust_df["repo_artifact_id"]
    )

    # Normalize outgoing edges per developer
    dev_edge_sum = edges_raw_df.groupby("git_user")["edge_weight"].transform("sum")
    edges_norm_df = edges_raw_df.copy()
    edges_norm_df["edge_weight_norm"] = edges_raw_df["edge_weight"] / dev_edge_sum
    edges_norm_df = edges_norm_df.fillna(0)  # Handle division by zero if sum is 0

    # --- 3. Iterative PageRank-like calculation ---

    repo_scores_df = repo_base_df.copy()
    repo_scores_df["repo_score_current"] = repo_scores_df["repo_score_base"]

    dev_contrib_cols = []

    for i in range(1, NUM_ITERATIONS + 1):
        # Merge current repo scores with normalized edges
        merged_df = pd.merge(
            edges_norm_df,
            repo_scores_df[["repo_artifact_id", "repo_score_current"]],
            on="repo_artifact_id",
            how="left",
        )

        # Calculate developer trust scores
        merged_df["dev_score_contrib"] = merged_df["edge_weight_norm"] * merged_df[
            "repo_score_current"
        ].fillna(0.0)
        dev_trust_df = (
            merged_df.groupby("git_user")["dev_score_contrib"].sum().reset_index()
        )
        dev_trust_df = dev_trust_df.rename(
            columns={"dev_score_contrib": f"dev_score_v{i}"}
        )

        # Propagate developer trust back to repos
        repo_from_dev_df = pd.merge(
            edges_norm_df, dev_trust_df, on="git_user", how="left"
        )
        repo_from_dev_df["repo_dev_contrib"] = repo_from_dev_df[
            "edge_weight_norm"
        ] * repo_from_dev_df[f"dev_score_v{i}"].fillna(0.0)

        repo_dev_contrib = (
            repo_from_dev_df.groupby("repo_artifact_id")["repo_dev_contrib"]
            .sum()
            .reset_index()
        )
        repo_dev_contrib = repo_dev_contrib.rename(
            columns={"repo_dev_contrib": f"repo_dev_contrib_v{i}"}
        )
        dev_contrib_cols.append(f"repo_dev_contrib_v{i}")

        # Merge contributions back into the main repo scores dataframe
        repo_scores_df = pd.merge(
            repo_scores_df, repo_dev_contrib, on="repo_artifact_id", how="left"
        )
        repo_scores_df[f"repo_dev_contrib_v{i}"] = repo_scores_df[
            f"repo_dev_contrib_v{i}"
        ].fillna(0.0)

        # Update the current repo score for the next iteration
        repo_scores_df["repo_score_current"] = (
            ALPHA * repo_scores_df["repo_score_base"]
        ) + ((1 - ALPHA) * repo_scores_df[f"repo_dev_contrib_v{i}"])

    # --- 4. Finalize and format output ---

    repo_scores_df = repo_scores_df.rename(
        columns={"repo_score_current": "final_score"}
    )

    # Ensure all dev contrib columns exist, even if loop is short
    for i in range(1, 3):
        col_name = f"repo_dev_contrib_v{i}"
        if col_name not in repo_scores_df.columns:
            repo_scores_df[col_name] = 0.0

    # Join to get URLs for all repos
    final_df = pd.merge(
        repo_scores_df,
        artifacts_df,
        left_on="repo_artifact_id",
        right_on="artifact_id",
        how="left",
    )

    # Calculate delta score
    final_df["delta_score"] = final_df["final_score"] - final_df["repo_score_base"]

    # Rank by final score
    final_df["trust_rank"] = (
        final_df["final_score"].rank(method="min", ascending=False).astype(int)
    )

    # Select and rename columns to match SQL output
    output_df = final_df[
        [
            "repo_artifact_id",
            "url",
            "is_pretrust",
            "repo_score_base",
            "repo_dev_contrib_v1",
            "repo_dev_contrib_v2",
            "final_score",
            "delta_score",
            "trust_rank",
        ]
    ].rename(
        columns={
            "repo_score_base": "base_score",
            "repo_dev_contrib_v1": "dev_contrib_v1",
            "repo_dev_contrib_v2": "dev_contrib_v2",
        }
    )

    # Sort by final score
    output_df = output_df.sort_values(by="final_score", ascending=False).reset_index(
        drop=True
    )

    return output_df


# Example usage:
# class MockContext:
#     def fetchdf(self, query):
#         # In a real scenario, this would connect to a database
#         print(f"Fetching data with query:\n{query}")
#         # Return mock dataframes for testing
#         if "pretrust" in query:
#             return pd.DataFrame({
#                 'repo_artifact_id': [1, 2], 'url': ['url1', 'url2'], 'repo_score_base': [1.0, 0.8]
#             })
#         if "graph" in query:
#             return pd.DataFrame({
#                 'git_user': ['dev1', 'dev1', 'dev2', 'dev3'],
#                 'repo_artifact_id': [1, 3, 3, 4],
#                 'edge_weight': [10, 5, 8, 12]
#             })
#         if "artifacts" in query:
#             return pd.DataFrame({
#                 'artifact_id': [1, 2, 3, 4],
#                 'url': ['url1', 'url2', 'url3', 'url4']
#             })
#         return pd.DataFrame()

# if __name__ == '__main__':
#     mock_context = MockContext()
#     results = discover_repos(mock_context)
#     print("\n--- Final Results ---")
#     print(results)
