"""
K-means clustering model for collection performance segmentation.

This Python model performs k-means clustering on collection performance features
to segment collections into performance tiers (e.g., Top, High, Mid, Low, Very Low).
"""

from __future__ import annotations

import typing as t

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples, silhouette_score
from sklearn.preprocessing import StandardScaler
from sqlmesh import ExecutionContext, model


@model(
    "oso.int_collection_performance_clusters",
    kind="full",
    columns={
        "collection_id": "TEXT",
        "collection_source": "TEXT",
        "collection_namespace": "TEXT",
        "collection_name": "TEXT",
        "collection_display_name": "TEXT",
        "sample_date": "DATE",
        "total_active_developers": "DOUBLE",
        "avg_active_developers_per_project": "DOUBLE",
        "active_dev_concentration": "DOUBLE",
        "total_stars": "DOUBLE",
        "avg_stars_per_project": "DOUBLE",
        "total_commits": "DOUBLE",
        "avg_commits_per_project": "DOUBLE",
        "total_forks": "DOUBLE",
        "total_contributors": "DOUBLE",
        "avg_contributors_per_project": "DOUBLE",
        "total_projects": "DOUBLE",
        "developer_density": "DOUBLE",
        "commits_per_developer": "DOUBLE",
        "star_appeal": "DOUBLE",
        "cluster": "INTEGER",
        "segment": "TEXT",
        "silhouette": "DOUBLE",
    },
    grain="collection_id",
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
    Execute k-means clustering on collection performance features.

    Args:
        context: SQLMesh execution context
        start: Start date (not used for FULL model)
        end: End date (not used for FULL model)
        execution_time: Execution time (not used for FULL model)
        **kwargs: Additional arguments

    Yields:
        DataFrame with clustering results
    """
    # Resolve the upstream table name (environment-aware)
    features_table = context.resolve_table("oso.int_collection_performance_features")

    # Read the features
    query = f"SELECT * FROM {features_table}"
    df = context.fetchdf(query)

    # If no data, yield nothing (use empty generator pattern)
    if df.empty:
        yield from ()
        return

    # Type enforcement
    df["collection_id"] = df["collection_id"].astype(str)
    df["collection_source"] = df["collection_source"].astype(str)
    df["collection_namespace"] = df["collection_namespace"].astype(str)
    df["collection_name"] = df["collection_name"].astype(str)
    df["collection_display_name"] = df["collection_display_name"].astype(str)
    df["sample_date"] = pd.to_datetime(df["sample_date"])

    # Fill nulls for numeric columns
    numeric_cols = [
        "total_active_developers",
        "avg_active_developers_per_project",
        "active_dev_concentration",
        "total_stars",
        "avg_stars_per_project",
        "total_commits",
        "avg_commits_per_project",
        "total_forks",
        "total_contributors",
        "avg_contributors_per_project",
        "total_projects",
        "developer_density",
        "commits_per_developer",
        "star_appeal",
    ]

    for col in numeric_cols:
        df[col] = df[col].fillna(0).astype(float)

    # Select features for clustering (higher weights = more important)
    feature_cols = [
        "total_active_developers",  # Weight: 2.5
        "total_stars",  # Weight: 1.5
        "total_commits",  # Weight: 2.0
        "total_contributors",  # Weight: 2.0
        "avg_active_developers_per_project",  # Weight: 1.5
        "developer_density",  # Weight: 1.8
        "commits_per_developer",  # Weight: 1.2
        "star_appeal",  # Weight: 1.0
    ]

    # Feature weights (emphasize developer activity and engagement)
    feature_weights = [2.5, 1.5, 2.0, 2.0, 1.5, 1.8, 1.2, 1.0]

    # Build feature matrix
    X = df[feature_cols].values

    # Standardize features (zero mean, unit variance)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Apply feature weights
    X_weighted = X_scaled * feature_weights

    # Determine optimal k using silhouette score
    n_samples = len(df)
    max_k = min(6, n_samples)  # Try up to 6 clusters, but not more than samples

    if n_samples < 3:
        # Too few samples for meaningful clustering
        df["cluster"] = 0
        df["segment"] = "Single Cluster"
        df["silhouette"] = 0.0
    else:
        best_score = -1
        best_labels = None

        # Try different values of k
        for k in range(3, max_k + 1):
            if k >= n_samples:
                break

            kmeans = KMeans(
                n_clusters=k,
                init="k-means++",
                n_init="auto",
                max_iter=300,
                random_state=42,
            )
            labels = kmeans.fit_predict(X_weighted)

            # Calculate silhouette score
            score = silhouette_score(X_weighted, labels)

            if score > best_score:
                best_score = score
                best_labels = labels

        # Assign cluster labels
        if best_labels is not None:
            df["cluster"] = best_labels

            # Calculate per-sample silhouette scores
            silhouettes = silhouette_samples(X_weighted, best_labels)
            df["silhouette"] = silhouettes
        else:
            # Fallback if clustering failed
            df["cluster"] = 0
            df["silhouette"] = 0.0

        # Assign meaningful segment names based on performance
        # Sort clusters by mean total_active_developers (proxy for overall performance)
        cluster_performance = (
            df.groupby("cluster")["total_active_developers"]
            .mean()
            .sort_values(ascending=True)  # type: ignore[call-overload]
        )

        # Map clusters to segment names
        segment_names = ["Very Low", "Low", "Mid", "High", "Top"]
        cluster_to_segment: dict[int, str] = {}

        for idx, cluster_id in enumerate(cluster_performance.index):
            # Assign names based on sorted order
            if idx < len(segment_names):
                cluster_to_segment[int(cluster_id)] = segment_names[idx]
            else:
                cluster_to_segment[int(cluster_id)] = f"Tier {idx + 1}"

        df["segment"] = df["cluster"].map(cluster_to_segment)  # type: ignore[arg-type]

    # Ensure output columns match schema and order
    output_df = df[
        [
            "collection_id",
            "collection_source",
            "collection_namespace",
            "collection_name",
            "collection_display_name",
            "sample_date",
            "total_active_developers",
            "avg_active_developers_per_project",
            "active_dev_concentration",
            "total_stars",
            "avg_stars_per_project",
            "total_commits",
            "avg_commits_per_project",
            "total_forks",
            "total_contributors",
            "avg_contributors_per_project",
            "total_projects",
            "developer_density",
            "commits_per_developer",
            "star_appeal",
            "cluster",
            "segment",
            "silhouette",
        ]
    ].copy()

    # Final type casting for safety
    output_df["collection_id"] = output_df["collection_id"].astype(str)
    output_df["collection_source"] = output_df["collection_source"].astype(str)
    output_df["collection_namespace"] = output_df["collection_namespace"].astype(str)
    output_df["collection_name"] = output_df["collection_name"].astype(str)
    output_df["collection_display_name"] = output_df["collection_display_name"].astype(
        str
    )
    output_df["cluster"] = output_df["cluster"].astype(int)
    output_df["segment"] = output_df["segment"].astype(str)
    output_df["silhouette"] = output_df["silhouette"].astype(float)

    for col in numeric_cols:
        output_df[col] = output_df[col].astype(float)

    # Yield the final DataFrame
    yield output_df  # type: ignore[misc]
