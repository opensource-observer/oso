"""
K-means clustering model for onchain project performance segmentation.

This Python model performs k-means clustering on onchain project performance features
to segment projects into performance tiers within collections (e.g., Blue Chip, Established,
High Activity, Emerging, Inactive).
"""

from __future__ import annotations

import typing as t

import numpy as np
import pandas as pd
from pandas.tseries.offsets import DateOffset
from scipy.spatial import distance
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples
from sklearn.preprocessing import StandardScaler
from sqlmesh import ExecutionContext, model

# ============================================================================
# CONFIGURATION VARIABLES
# ============================================================================

# Metric name mappings (display name -> metric_model in database)
METRIC_MAPPINGS = {
    "TVL": "defillama_tvl",
    "Contract Invocations": "contract_invocations",
    "Addresses": "active_addresses_aggregation",
    "Farcaster Users": "farcaster_users",
    "Layer2 Gas Fees": "layer2_gas_fees",
    "Amortized Layer2 Gas Fees": "layer2_gas_fees_amortized",
}

# Clustering thresholds
BLUE_CHIP_TVL_THRESHOLD = 10_000_000  # $10M
INACTIVE_CONTRACT_INVOCATIONS = 100
KMEANS_CLUSTERS = 3
MASTER_MODEL_MONTHS = 6  # Training window for master model

# Cluster names
CLUSTER_NAMES = {
    "blue_chip": "Blue Chip",
    "inactive": "Inactive",
    "established": "Established",
    "high_activity": "High Activity",
    "emerging": "Emerging",
    "not_active": "Not Active",
}

# Chains to analyze (empty list = all chains)
TARGET_CHAINS: list[str] = []  # e.g., ['BASE', 'OPTIMISM']

# Feature columns to use for clustering (keys from METRIC_MAPPINGS)
FEATURE_KEYS = [
    "TVL",
    "Contract Invocations",
    "Addresses",
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_period_slice(
    df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> pd.DataFrame:
    """Extract data for a specific time period."""
    mask = (df["sample_date"] >= start) & (df["sample_date"] < end)
    return df.loc[mask].copy()


def pivot_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert metric rows to feature columns.

    Input: Rows with metric_model and amount
    Output: Columns for each metric in METRIC_MAPPINGS
    """
    # Filter to only metrics we care about
    metric_models = list(METRIC_MAPPINGS.values())
    df_filtered = df[df["metric_model"].isin(metric_models)].copy()

    if df_filtered.empty:
        return pd.DataFrame()

    # Create reverse mapping (metric_model -> display name)
    reverse_mapping = {v: k for k, v in METRIC_MAPPINGS.items()}
    df_filtered["metric_display"] = df_filtered["metric_model"].map(reverse_mapping)  # type: ignore[arg-type]

    # Pivot to get features as columns
    pivot_df = df_filtered.pivot_table(
        index=[
            "collection_id",
            "collection_source",
            "collection_namespace",
            "collection_name",
            "collection_display_name",
            "project_id",
            "project_source",
            "project_namespace",
            "project_name",
            "project_display_name",
            "chain",
            "sample_date",
        ],
        columns="metric_display",
        values="amount",
        aggfunc="sum",
    ).reset_index()

    # Fill missing metrics with 0
    for metric_name in METRIC_MAPPINGS.keys():
        if metric_name not in pivot_df.columns:
            pivot_df[metric_name] = 0.0

    return pivot_df


def scale_features(
    df: pd.DataFrame,
    feature_labels: list[str],
    tvl_threshold: float,
    inactive_threshold: float,
) -> tuple[
    pd.DataFrame | None,
    pd.DataFrame,
    pd.DataFrame,
    np.ndarray | None,
    list[str],
]:
    """
    Segment projects and scale features for clustering.

    Returns:
        - to_cluster: DataFrame of projects to cluster
        - blue_chip: DataFrame of blue chip projects
        - inactive: DataFrame of inactive projects
        - X: Scaled feature matrix
        - log_cols: List of log-transformed column names
    """
    df_copy = df.copy()

    # Segment blue chips (high TVL)
    blue = df_copy[df_copy["TVL"] >= tvl_threshold].copy()  # type: ignore[call-overload]
    blue["cluster"] = CLUSTER_NAMES["blue_chip"]

    # Segment inactive (low contract invocations)
    inactive = df_copy[df_copy["Contract Invocations"] < inactive_threshold].copy()  # type: ignore[call-overload]
    inactive["cluster"] = CLUSTER_NAMES["inactive"]

    # Projects to cluster (not blue chip, not inactive)
    to_cluster = df_copy[
        (df_copy["TVL"] < tvl_threshold)
        & (df_copy["Contract Invocations"] >= inactive_threshold)
    ].copy()

    if to_cluster.empty:
        return None, blue, inactive, None, []  # type: ignore[return-value]

    # Log-transform features
    log_cols = []
    for lbl in feature_labels:
        if lbl in to_cluster.columns:
            lc = f"log_{lbl}"
            to_cluster[lc] = np.log10(to_cluster[lbl] + 1e-6)
            log_cols.append(lc)

    if not log_cols:
        return None, blue, inactive, None, []  # type: ignore[return-value]

    # Scale features
    scaler = StandardScaler()
    X = scaler.fit_transform(to_cluster[log_cols])

    return to_cluster, blue, inactive, X, log_cols  # type: ignore[return-value]


def train_master_model(
    df_master: pd.DataFrame,
    feature_labels: list[str],
    n_clusters: int,
    tvl_threshold: float,
    inactive_threshold: float,
) -> tuple[np.ndarray, dict[int, str]]:
    """
    Train the master K-means model and create cluster name mapping.

    Returns:
        - centers: Cluster centroids
        - cluster_map: Mapping from cluster ID to cluster name
    """
    df_c, blue, inactive, X, log_cols = scale_features(
        df_master, feature_labels, tvl_threshold, inactive_threshold
    )

    if df_c is None or X is None:
        # Not enough data to train
        return np.array([]), {}

    # Train K-means
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    kmeans.fit(X)
    centers = kmeans.cluster_centers_

    # Map clusters to meaningful names based on feature values
    # Identify clusters by TVL and Contract Invocations
    tvl_idx = log_cols.index("log_TVL") if "log_TVL" in log_cols else 0
    ci_idx = (
        log_cols.index("log_Contract Invocations")
        if "log_Contract Invocations" in log_cols
        else 1
    )

    # Established = highest TVL
    established = int(np.argmax(centers[:, tvl_idx]))

    # High Activity = highest contract invocations (among remaining)
    remaining = [i for i in range(n_clusters) if i != established]
    if remaining:
        high_activity = remaining[int(np.argmax(centers[remaining, ci_idx]))]
    else:
        high_activity = established

    # Emerging = the rest
    emerging = [i for i in range(n_clusters) if i not in [established, high_activity]]

    # Build cluster map
    cluster_map = {
        established: CLUSTER_NAMES["established"],
        high_activity: CLUSTER_NAMES["high_activity"],
    }
    for idx in emerging:
        cluster_map[idx] = CLUSTER_NAMES["emerging"]

    return centers, cluster_map


def assign_clusters(
    df_period: pd.DataFrame,
    centers: np.ndarray,
    cluster_map: dict[int, str],
    feature_labels: list[str],
    tvl_threshold: float,
    inactive_threshold: float,
) -> pd.DataFrame:
    """
    Assign clusters to projects in a given period using trained model.
    """
    df_c, blue, inactive, X, log_cols = scale_features(
        df_period, feature_labels, tvl_threshold, inactive_threshold
    )

    parts = []

    # Assign clusters to projects that need K-means
    if df_c is not None and X is not None and len(centers) > 0:
        dists = distance.cdist(X, centers, "euclidean")
        idx = np.argmin(dists, axis=1)
        df_c["cluster"] = [cluster_map[i] for i in idx]

        # Calculate silhouette scores
        if len(df_c) > 1 and len(np.unique(idx)) > 1:
            silhouettes = silhouette_samples(X, idx)
            df_c["silhouette"] = silhouettes
        else:
            df_c["silhouette"] = 0.0

        parts.append(df_c)

    # Add pre-segmented projects
    if not blue.empty:
        blue["silhouette"] = 1.0  # High confidence
        parts.append(blue)

    if not inactive.empty:
        inactive["silhouette"] = 1.0  # High confidence
        parts.append(inactive)

    if not parts:
        return pd.DataFrame()

    return pd.concat(parts, ignore_index=True, sort=False)


def build_cluster_history(
    df_all: pd.DataFrame,
    snapshot_date: pd.Timestamp,
    master_months: int,
    n_clusters: int,
    tvl_threshold: float,
    inactive_threshold: float,
) -> pd.DataFrame:
    """
    Build historical cluster assignments for all projects.

    Trains a master model on recent data, then applies it to historical periods.
    """
    history = []

    # Get unique projects and collection/chain combinations
    project_keys = df_all[
        [
            "collection_id",
            "collection_source",
            "collection_namespace",
            "collection_name",
            "collection_display_name",
            "project_id",
            "project_source",
            "project_namespace",
            "project_name",
            "project_display_name",
            "chain",
        ]
    ].drop_duplicates()

    # Get unique collection+chain combinations
    collection_chains = df_all[["collection_id", "chain"]].drop_duplicates()

    # Process each collection+chain combination separately
    for _, cc_row in collection_chains.iterrows():
        collection_id = cc_row["collection_id"]
        chain = cc_row["chain"]

        # Filter to this collection+chain
        df_subset = df_all[
            (df_all["collection_id"] == collection_id) & (df_all["chain"] == chain)
        ].copy()

        if df_subset.empty:
            continue

        # Get periods to analyze
        periods = [
            (
                snapshot_date - DateOffset(months=i + 1),
                snapshot_date - DateOffset(months=i),
            )
            for i in range(master_months)
        ]

        # Train master model on recent data
        df_master = get_period_slice(
            df_subset,  # type: ignore[arg-type]
            snapshot_date - DateOffset(months=master_months),
            snapshot_date,
        )

        if df_master.empty:
            continue

        centers, cmap = train_master_model(
            df_master,
            FEATURE_KEYS,
            n_clusters,
            tvl_threshold,
            inactive_threshold,
        )

        # Apply to each period
        for start, end in reversed(periods):
            # Create scaffold with all projects
            scaffold = project_keys[
                (project_keys["collection_id"] == collection_id)
                & (project_keys["chain"] == chain)
            ].copy()
            scaffold["snapshot_date"] = pd.to_datetime(end)
            scaffold["sample_date"] = pd.to_datetime(start)

            # Get data for this period
            df_per = get_period_slice(df_subset, start, end)  # type: ignore[arg-type]

            if not df_per.empty and len(centers) > 0:
                assigned = assign_clusters(
                    df_per,
                    centers,
                    cmap,
                    FEATURE_KEYS,
                    tvl_threshold,
                    inactive_threshold,
                )

                if not assigned.empty:
                    assigned["snapshot_date"] = pd.to_datetime(end)

                    # Merge with scaffold
                    merged = scaffold.merge(  # type: ignore[assignment]
                        assigned,
                        on=[
                            "collection_id",
                            "collection_source",
                            "collection_namespace",
                            "collection_name",
                            "collection_display_name",
                            "project_id",
                            "project_source",
                            "project_namespace",
                            "project_name",
                            "project_display_name",
                            "chain",
                            "snapshot_date",
                            "sample_date",
                        ],
                        how="left",
                    )
                else:
                    merged = scaffold
            else:
                merged = scaffold

            # Fill missing clusters
            merged["cluster"] = merged["cluster"].fillna(CLUSTER_NAMES["not_active"])  # type: ignore[union-attr]
            merged["silhouette"] = merged["silhouette"].fillna(0.0)  # type: ignore[union-attr]

            # Fill missing feature values with 0
            for metric_name in METRIC_MAPPINGS.keys():
                if metric_name not in merged.columns:  # type: ignore[operator]
                    merged[metric_name] = 0.0
                else:
                    merged[metric_name] = merged[metric_name].fillna(0.0)  # type: ignore[union-attr]

            history.append(merged)

    if not history:
        return pd.DataFrame()

    return pd.concat(history, ignore_index=True)


# ============================================================================
# SQLMESH MODEL
# ============================================================================


@model(
    "oso.int_onchain_project_performance_clusters",
    kind="full",
    columns={
        "collection_id": "TEXT",
        "collection_source": "TEXT",
        "collection_namespace": "TEXT",
        "collection_name": "TEXT",
        "collection_display_name": "TEXT",
        "project_id": "TEXT",
        "project_source": "TEXT",
        "project_namespace": "TEXT",
        "project_name": "TEXT",
        "project_display_name": "TEXT",
        "chain": "TEXT",
        "sample_date": "DATE",
        "snapshot_date": "DATE",
        "tvl": "DOUBLE",
        "contract_invocations": "DOUBLE",
        "addresses": "DOUBLE",
        "farcaster_users": "DOUBLE",
        "layer2_gas_fees": "DOUBLE",
        "amortized_layer2_gas_fees": "DOUBLE",
        "cluster": "TEXT",
        "silhouette": "DOUBLE",
    },
    grain=("collection_id", "project_id", "chain", "sample_date"),
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
    Execute k-means clustering on onchain project performance features.

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
    ranked_table = context.resolve_table("oso.int_ranked_projects_by_collection")

    # Build query to get onchain metrics
    metric_models = list(METRIC_MAPPINGS.values())
    metric_list = ", ".join([f"'{m}'" for m in metric_models])

    chain_filter = ""
    if TARGET_CHAINS:
        chain_list = ", ".join([f"'{c}'" for c in TARGET_CHAINS])
        chain_filter = f"AND metric_event_source IN ({chain_list})"

    query = f"""
    SELECT
        collection_id,
        collection_source,
        collection_namespace,
        collection_name,
        collection_display_name,
        project_id,
        project_source,
        project_namespace,
        project_name,
        project_display_name,
        metric_event_source AS chain,
        sample_date,
        metric_model,
        amount
    FROM {ranked_table}
    WHERE
        metric_model IN ({metric_list})
        {chain_filter}
    """

    df = context.fetchdf(query)

    # If no data, yield empty
    if df.empty:
        yield from ()
        return

    # Convert types
    df["sample_date"] = pd.to_datetime(df["sample_date"])

    # Pivot metrics to feature columns
    df_features = pivot_metrics(df)

    if df_features.empty:
        yield from ()
        return

    # Get the most recent snapshot date
    max_date = df_features["sample_date"].max()
    snapshot_date = pd.Timestamp(max_date)  # type: ignore[arg-type]

    # Build cluster history
    df_clustered = build_cluster_history(
        df_features,
        snapshot_date,
        MASTER_MODEL_MONTHS,
        KMEANS_CLUSTERS,
        BLUE_CHIP_TVL_THRESHOLD,
        INACTIVE_CONTRACT_INVOCATIONS,
    )

    if df_clustered.empty:
        yield from ()
        return

    # Prepare output with correct column names (lowercase with underscores)
    output_df = df_clustered[
        [
            "collection_id",
            "collection_source",
            "collection_namespace",
            "collection_name",
            "collection_display_name",
            "project_id",
            "project_source",
            "project_namespace",
            "project_name",
            "project_display_name",
            "chain",
            "sample_date",
            "snapshot_date",
            "TVL",
            "Contract Invocations",
            "Addresses",
            "Farcaster Users",
            "Layer2 Gas Fees",
            "Amortized Layer2 Gas Fees",
            "cluster",
            "silhouette",
        ]
    ].copy()

    # Rename feature columns to match schema
    output_df = output_df.rename(  # type: ignore[call-overload]
        columns={
            "TVL": "tvl",
            "Contract Invocations": "contract_invocations",
            "Addresses": "addresses",
            "Farcaster Users": "farcaster_users",
            "Layer2 Gas Fees": "layer2_gas_fees",
            "Amortized Layer2 Gas Fees": "amortized_layer2_gas_fees",
        }
    )

    # Type enforcement
    for col in [
        "collection_id",
        "collection_source",
        "collection_namespace",
        "collection_name",
        "collection_display_name",
        "project_id",
        "project_source",
        "project_namespace",
        "project_name",
        "project_display_name",
        "chain",
        "cluster",
    ]:
        output_df[col] = output_df[col].astype(str)

    for col in [
        "tvl",
        "contract_invocations",
        "addresses",
        "farcaster_users",
        "layer2_gas_fees",
        "amortized_layer2_gas_fees",
        "silhouette",
    ]:
        output_df[col] = output_df[col].astype(float)

    output_df["sample_date"] = pd.to_datetime(output_df["sample_date"])
    output_df["snapshot_date"] = pd.to_datetime(output_df["snapshot_date"])

    # Yield the final DataFrame
    yield output_df  # type: ignore[misc]
