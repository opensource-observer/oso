from __future__ import annotations

import typing as t
from dataclasses import dataclass
from typing import List, Optional, Tuple, cast

import numpy as np
import pandas as pd
from scipy.spatial import distance
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_samples
from sklearn.preprocessing import StandardScaler
from sqlglot import exp
from sqlmesh import ExecutionContext, model

# =============================================================================
# Configuration & Data Structures
# =============================================================================

PROJECT_COL = "project_id"
DATE_COL = "sample_date"
METRIC_COL = "metric_model"
VALUE_COL = "amount"


@dataclass(frozen=True)
class MetricSpec:
    """Specification for a metric and how it should be used in clustering."""

    id: str
    role: str = "feature"  # "feature", "output_only", "segment_only"
    transform: str = "log1p"  # "log1p", "log10", "linear"


@dataclass
class ModelArtifact:
    """Trained k-means model artifacts for inference."""

    centers: np.ndarray
    feature_cols: List[str]
    scaler_mean_: Optional[np.ndarray]
    scaler_scale_: Optional[np.ndarray]
    training_start: Optional[pd.Timestamp]
    training_end: Optional[pd.Timestamp]


# =============================================================================
# Helper Functions
# =============================================================================


def _ensure_numeric(df: pd.DataFrame, cols: List[str]) -> None:
    """Convert columns to numeric, coercing errors to 0."""
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)


def _clip_range_to_data(
    start_str: Optional[str],
    end_str: Optional[str],
    data_start: Optional[pd.Timestamp],
    data_end: Optional[pd.Timestamp],
) -> Tuple[pd.Timestamp, pd.Timestamp]:
    # Build start
    if start_str is not None:
        try:
            s = pd.Timestamp(start_str)
        except Exception:
            s = pd.Timestamp.min
    elif data_start is not None and not pd.isna(data_start):
        s = data_start
    else:
        s = pd.Timestamp.min
    # Build end
    if end_str is not None:
        try:
            e = pd.Timestamp(end_str)
        except Exception:
            e = pd.Timestamp.max
    elif data_end is not None and not pd.isna(data_end):
        e = data_end
    else:
        e = pd.Timestamp.max
    # Normalize potential NaT
    if pd.isna(s):
        s = pd.Timestamp.min
    if pd.isna(e):
        e = pd.Timestamp.max
    # Clip
    if data_start is not None and not pd.isna(data_start):
        s = max(s, data_start)
    if data_end is not None and not pd.isna(data_end):
        e = min(e, data_end)
    return s, e


def pivot_metrics(df: pd.DataFrame, metric_models: List[str]) -> pd.DataFrame:
    """
    Transform long-format metrics data into wide format with one column per metric.

    Args:
        df: DataFrame in long format with columns [project_id, sample_date, metric_model, amount]
        metric_models: List of metric names to pivot

    Returns:
        DataFrame in wide format with columns [project_id, sample_date, <metric1>, <metric2>, ...]
    """
    if df.empty:
        return pd.DataFrame()
    df = df[df[METRIC_COL].isin(metric_models)].copy()
    wide_raw = df.pivot_table(
        index=[PROJECT_COL, DATE_COL],
        columns=METRIC_COL,
        values=VALUE_COL,
        aggfunc="sum",
        observed=True,
    ).reset_index()
    wide: pd.DataFrame = wide_raw

    for m in metric_models:
        if m not in wide.columns:
            wide[m] = 0.0
        wide[m] = pd.to_numeric(wide[m], errors="coerce").fillna(0)
    wide[DATE_COL] = pd.to_datetime(wide[DATE_COL])
    return wide


def build_features(
    df: pd.DataFrame, metrics: List[MetricSpec]
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Apply transformations to raw metrics to create model features.

    Args:
        df: DataFrame with raw metric columns
        metrics: List of MetricSpec defining which metrics to use and how to transform them

    Returns:
        Tuple of (DataFrame with added feature columns, list of feature column names)
    """
    dfc = df.copy()
    metric_ids = [
        m.id for m in metrics if m.role in ("feature", "segment_only", "output_only")
    ]
    for m in metric_ids:
        if m not in dfc.columns:
            dfc[m] = 0.0
    _ensure_numeric(dfc, metric_ids)
    feature_cols: List[str] = []
    for m in metrics:
        if m.role != "feature":
            continue
        base = m.id
        if m.transform == "log1p":
            col = f"log1p_{base}"
            dfc[col] = np.log1p(dfc[base].astype(float))
        elif m.transform in ("log", "log10"):
            col = f"log10_{base}"
            dfc[col] = np.log10(dfc[base].astype(float) + 1e-6)
        elif m.transform == "linear":
            col = f"linear_{base}"
            dfc[col] = dfc[base].astype(float)
        else:
            raise ValueError(f"unknown transform: {m.transform}")
        feature_cols.append(col)
    return dfc, feature_cols


# =============================================================================
# Model Training & Assignment
# =============================================================================


def train_master(
    df_train: pd.DataFrame,
    metrics: List[MetricSpec],
    n_clusters: int,
    random_state: int = 42,
) -> ModelArtifact:
    """
    Train a k-means clustering model on the training data.

    Args:
        df_train: Training DataFrame with metric columns
        metrics: List of MetricSpec defining features
        n_clusters: Number of clusters for k-means
        random_state: Random seed for reproducibility

    Returns:
        ModelArtifact containing cluster centers and scaler parameters
    """
    feats, feature_cols = build_features(df_train, metrics)
    # enforce deterministic feature order exactly as produced by build_features
    X_in = feats[feature_cols].values
    if X_in.shape[0] < n_clusters or X_in.shape[1] == 0:
        return ModelArtifact(
            centers=np.array([]),
            feature_cols=[],
            scaler_mean_=np.array([]),
            scaler_scale_=np.array([]),
            training_start=None,
            training_end=None,
        )
    scaler = StandardScaler()
    X = scaler.fit_transform(X_in)
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init="auto")
    kmeans.fit(X)

    # Extract training range as Optional Timestamps
    min_date_raw = df_train[DATE_COL].min()
    max_date_raw = df_train[DATE_COL].max()
    training_start_opt = None if pd.isna(min_date_raw) else pd.Timestamp(min_date_raw)
    training_end_opt = None if pd.isna(max_date_raw) else pd.Timestamp(max_date_raw)

    return ModelArtifact(
        centers=kmeans.cluster_centers_,
        feature_cols=feature_cols,
        scaler_mean_=cast(np.ndarray, scaler.mean_),
        scaler_scale_=cast(np.ndarray, scaler.scale_),
        training_start=training_start_opt,
        training_end=training_end_opt,
    )


def assign_month(
    df_month: pd.DataFrame,
    metrics: List[MetricSpec],
    artifact: ModelArtifact,
    compute_silhouette: bool = True,
) -> pd.DataFrame:
    """
    Assign cluster labels to projects for a single month using a trained model.

    Args:
        df_month: DataFrame with data for one month
        metrics: List of MetricSpec defining features
        artifact: Trained ModelArtifact from train_master
        compute_silhouette: Whether to compute silhouette scores

    Returns:
        DataFrame with added cluster_id and silhouette columns
    """
    if df_month.empty:
        return pd.DataFrame()

    feats, feature_cols = build_features(df_month, metrics)
    for c in feature_cols:
        col_data = pd.to_numeric(feats[c], errors="coerce")
        col_data = col_data.replace([np.inf, -np.inf], 0)
        feats[c] = col_data.fillna(0)

    if artifact.centers.size == 0:
        out = feats.copy()
        out["cluster_id"] = np.nan
        out["silhouette"] = 0.0
        return out

    if artifact.scaler_mean_ is None or artifact.scaler_scale_ is None:
        out = feats.copy()
        out["cluster_id"] = np.nan
        out["silhouette"] = 0.0
        return out

    if feature_cols != artifact.feature_cols:
        common = [c for c in feature_cols if c in artifact.feature_cols]
        if not common:
            out = feats.copy()
            out["cluster_id"] = np.nan
            out["silhouette"] = 0.0
            return out
        X = feats[common].values
        idxs = [artifact.feature_cols.index(c) for c in common]
        mean = artifact.scaler_mean_[idxs]
        scale = artifact.scaler_scale_[idxs]
        Xs = (X - mean) / np.where(scale == 0, 1.0, scale)
        d = distance.cdist(Xs, artifact.centers[:, idxs], "euclidean")
    else:
        X = feats[feature_cols].values
        mean = artifact.scaler_mean_
        scale = artifact.scaler_scale_
        Xs = (X - mean) / np.where(scale == 0, 1.0, scale)
        d = distance.cdist(Xs, artifact.centers, "euclidean")

    lbl = np.argmin(d, axis=1)
    out = feats.copy()
    out["cluster_id"] = lbl.astype(int)

    # SAFE silhouette: 2 ≤ n_labels ≤ n_samples-1
    if compute_silhouette:
        n_samples = len(lbl)
        n_labels = len(np.unique(lbl))
        if n_labels >= 2 and n_samples > n_labels:
            out["silhouette"] = silhouette_samples(Xs, lbl)
        else:
            out["silhouette"] = 0.0
    else:
        out["silhouette"] = 0.0
    return out


def build_monthly_history_full_range(
    df_wide: pd.DataFrame,
    metrics: List[MetricSpec],
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    n_clusters: int,
    random_state: int = 42,
    compute_silhouette: bool = True,
) -> pd.DataFrame:
    """
    Train a clustering model and assign all projects across all months to clusters.

    Creates a complete grid of all projects × all months, trains k-means on the
    specified training period, and assigns cluster labels to all project-months.

    Args:
        df_wide: DataFrame in wide format (output of pivot_metrics) with metric columns
        metrics: List of MetricSpec defining features and output metrics
        train_start: Start date for training period (inclusive)
        train_end: End date for training period (inclusive)
        n_clusters: Number of clusters for k-means
        random_state: Random seed for reproducibility
        compute_silhouette: Whether to compute silhouette scores

    Returns:
        DataFrame with columns [project_id, sample_date, cluster_id, silhouette, <metrics>]
        for all projects across all months in the input data
    """
    if df_wide.empty:
        return pd.DataFrame()

    df_wide = df_wide.copy()
    df_wide[DATE_COL] = pd.to_datetime(df_wide[DATE_COL])

    # compact metrics
    metric_ids = [
        m.id for m in metrics if m.role in ("feature", "segment_only", "output_only")
    ]
    for m in metric_ids:
        if m in df_wide.columns:
            col_numeric = pd.to_numeric(df_wide[m], errors="coerce")
            df_wide[m] = col_numeric.fillna(0).astype("float64")

    # inclusive training slice
    t0, t1 = pd.to_datetime(train_start), pd.to_datetime(train_end)
    df_train = df_wide[(df_wide[DATE_COL] >= t0) & (df_wide[DATE_COL] <= t1)].copy()

    if df_train.empty:
        return pd.DataFrame()

    # cap k to available samples
    n_train = len(df_train)
    k_used = min(n_clusters, n_train) if n_train > 0 else n_clusters
    # silhouette only makes sense with >=2 samples and >=2 labels
    compute_sil = compute_silhouette and n_train >= 2 and k_used >= 2

    artifact = train_master(df_train, metrics, k_used, random_state=random_state)

    # full grid: all projects × all months present
    roster = df_wide[[PROJECT_COL]].drop_duplicates().copy()
    months = pd.DataFrame({DATE_COL: sorted(df_wide[DATE_COL].unique())})
    roster["_k"] = 1
    months["_k"] = 1
    grid = roster.merge(months, on="_k").drop(columns="_k")

    # assign by month
    parts = []
    for m_val, g in df_wide.groupby(DATE_COL, sort=True, group_keys=False):
        g_assigned = assign_month(g, metrics, artifact, compute_silhouette=compute_sil)
        parts.append(g_assigned)
    assigned = pd.concat(parts, ignore_index=True) if parts else df_wide.iloc[0:0]

    merged = grid.merge(assigned, on=[PROJECT_COL, DATE_COL], how="left")

    # ensure metric cols & stable dtypes
    for spec in metrics:
        if spec.id not in merged.columns:
            merged[spec.id] = 0.0
        col_numeric = pd.to_numeric(merged[spec.id], errors="coerce")
        merged[spec.id] = col_numeric.fillna(0).astype("float64")

    merged["cluster_id"] = merged["cluster_id"].astype("Int64")
    sil_col = merged["silhouette"]
    merged["silhouette"] = sil_col.fillna(0.0)

    metric_cols = [m.id for m in metrics]
    cols = [PROJECT_COL, DATE_COL, "cluster_id", "silhouette"] + metric_cols

    result: pd.DataFrame = merged[cols]
    result = result[result["cluster_id"].notna()]
    return result


# =============================================================================
# Base Query Definition
# =============================================================================


def generate_query(
    collection_name: str,
    chains: List[str],
    metrics: List[str],
    context: ExecutionContext,
) -> str:
    """Generate SQL query to fetch metrics data."""
    ranked_table = context.resolve_table("oso.int_ranked_projects_by_collection")
    metric_list = ", ".join([f"'{m}'" for m in metrics])
    chain_list = ", ".join([f"'{c}'" for c in chains])
    sql = f"""
    SELECT
      sample_date,
      project_id,
      metric_model,
      amount
    FROM {ranked_table}
    WHERE metric_model IN ({metric_list})
      AND metric_event_source IN ({chain_list})
      AND collection_name = '{collection_name}'
    """
    return sql


# =============================================================================
# SQLMesh Model Definition
# =============================================================================


@model(
    "oso.int_onchain_project_performance_clusters",
    kind="full",
    columns={
        "project_id": exp.DataType.build("TEXT"),
        "sample_date": exp.DataType.build("DATE"),
        "cluster_id": exp.DataType.build("BIGINT"),
        "silhouette": exp.DataType.build("DOUBLE"),
        # Metric columns
        "contract_invocations": exp.DataType.build("DOUBLE"),
        "active_addresses_aggregation": exp.DataType.build("DOUBLE"),
        "farcaster_users": exp.DataType.build("DOUBLE"),
        "layer2_gas_fees": exp.DataType.build("DOUBLE"),
        "layer2_gas_fees_amortized": exp.DataType.build("DOUBLE"),
    },
    grain=("project_id", "cluster_id", "sample_date"),
    audits=[
        ("has_at_least_n_rows", {"threshold": 1}),
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

    This model segments projects into performance clusters based on onchain metrics.
    The clustering is trained on a specified time period and applied to all project-months.

    Args:
        context: SQLMesh execution context
        start: Training period start date (optional, defaults to earliest date in data)
        end: Training period end date (optional, defaults to latest date in data)
        execution_time: Execution time (not used for FULL model)
        **kwargs: Additional arguments

    Yields:
        DataFrame with clustering results including cluster_id and silhouette scores
    """
    # =========================================================================
    # Configuration - Modify these to change clustering behavior
    # =========================================================================

    n_clusters = 5
    start = "2024-04-01"
    end = "2024-10-01"

    collection_name = "optimism"
    chains = ["OPTIMISM", "BASE", "UNICHAIN", "INK", "MODE", "SONEIUM", "ZORA"]
    feature_metrics = [
        MetricSpec(id="contract_invocations", role="feature", transform="log1p"),
        MetricSpec(
            id="active_addresses_aggregation", role="feature", transform="log1p"
        ),
        MetricSpec(id="farcaster_users", role="feature", transform="log1p"),
        MetricSpec(id="layer2_gas_fees", role="feature", transform="log1p"),
        MetricSpec(id="layer2_gas_fees_amortized", role="feature", transform="log1p"),
    ]

    # =========================================================================
    # Execution Logic
    # =========================================================================

    metric_models = [m.id for m in feature_metrics]
    query = generate_query(
        collection_name=collection_name,
        chains=chains,
        metrics=metric_models,
        context=context,
    )

    df_features = context.fetchdf(query)

    if df_features.empty:
        yield from ()
        return

    # Pivot from long to wide format
    df_wide = pivot_metrics(df_features, metric_models)

    if df_wide.empty:
        yield from ()
        return

    # Determine training date range
    df_wide["sample_date"] = pd.to_datetime(df_wide["sample_date"])

    # Extract scalar date bounds and clip requested range to data (no helper)
    sdates = df_wide["sample_date"]
    if sdates.empty:
        data_start_opt: Optional[pd.Timestamp] = None
        data_end_opt: Optional[pd.Timestamp] = None
    else:
        _min = sdates.min()
        _max = sdates.max()
        data_start_opt = None if pd.isna(_min) else pd.Timestamp(_min)
        data_end_opt = None if pd.isna(_max) else pd.Timestamp(_max)
    train_start, train_end = _clip_range_to_data(
        start_str=start, end_str=end, data_start=data_start_opt, data_end=data_end_opt
    )

    # Perform clustering
    df_clustered = build_monthly_history_full_range(
        df_wide=df_wide,
        metrics=feature_metrics,
        train_start=train_start,
        train_end=train_end,
        n_clusters=n_clusters,
        random_state=42,
        compute_silhouette=True,
    )

    if df_clustered.empty:
        yield from ()
        return

    yield df_clustered
